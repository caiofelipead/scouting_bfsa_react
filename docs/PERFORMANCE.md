# Performance & Footprint Notes

This document captures the conventions the backend follows to stay within
the Render Standard (2 GB) memory budget and to keep cold-start latency
low. Future contributors: please honour the patterns below or document a
deliberate exception.

---

## Lazy imports for heavy ML libraries

Modules under `backend/services/` that depend on `xgboost`, `socceraction`,
`statsmodels`, or any other library that ships native code or > 20 MB of
Python should follow this pattern:

```python
# Top of file: cheap availability probe — no native code is loaded yet.
import importlib.util as _importlib_util
HAS_XGB = _importlib_util.find_spec("xgboost") is not None
```

```python
# Inside the method that actually fits/predicts:
def fit(self, X, y):
    if HAS_XGB:
        import xgboost as xgb  # lazy: ~80 MB native lib
        self.model = xgb.XGBRegressor(...)
```

Why: `import xgboost` allocates ~80 MB of native memory on first call,
even if the model is never trained. With the previous eager-import
pattern every Render worker paid that cost on boot.

Currently applied in:

- `services/vaep_engine.py` — socceraction (spadl/features/labels) and
  xgboost are imported inside `_run_full_pipeline`, `_convert_to_spadl`
  and `_train_models`.
- `services/scouting_intelligence.py` — xgboost imported inside
  `MarketValueModel.fit`.
- `services/predictive_engine.py` — statsmodels imported inside
  `WinProbabilityModel.fit`; xgboost was unused at module level.

---

## Float32 dtype convention

Player and event DataFrames are wide (60–120 numeric columns) and tall
(thousands of rows). Defaulting to `float64` doubles the in-memory size
for no statistical benefit at the precision of scouting metrics.

`services/data_loader.downcast_numeric(df)` converts every `float64`
column to `float32` and every `int64` column to `int32`. It is invoked
automatically at the end of `main._coerce_numeric_columns`, so any
DataFrame that goes through the standard load pipeline is already
downcast by the time it reaches the engines.

If you load a frame outside that pipeline (e.g. ad-hoc CSV in a script),
call `downcast_numeric(df)` after type coercion.

---

## PostgreSQL connection pool

`services/database.py` exposes:

- `get_connection()` / `release_connection()` — leases a healthy
  connection from a `SimpleConnectionPool(minconn=1, maxconn=5)`.
  **Each checkout is validated with `SELECT 1`** to detect connections
  that the server has silently dropped (Neon idle timeout, network
  blip). Dead connections are dropped from the pool, not recycled.
- `get_conn()` — context manager that wraps the lease/release pair and
  automatically rolls back on exception, force-closing the socket on
  `OperationalError`/`InterfaceError` so the next caller never inherits
  a broken connection.

Use `get_conn()` for new code:

```python
from services.database import get_conn

def list_users():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM users")
            return cur.fetchall()
```

Why: previously a single Neon idle-timeout would poison the pool and
every subsequent background sync logged `connection already closed`
until the worker restarted.

---

## TTLCache caps

Every in-process cache MUST have an explicit `maxsize`. The custom
`_TTLCache` in `main.py` defaults to `maxsize=128` with FIFO eviction;
all `cachetools.TTLCache` instances elsewhere already declare a maxsize
(see `services/thesportsdb.py`, `routes/proxy.py`).

Don't introduce caches with `maxsize=float("inf")` — they shadow leaks
and inflate RSS proportionally to traffic.

---

## GC after sheet-wise sync

Background syncs in `services/sync_sheets.py` (`sync_all_sheets`,
`sync_coach_sheets`, `sync_single_sheet`) explicitly `del df` and call
`gc.collect()` after each tab. Without this, peak RSS during a full
rotation grew to ~2× the size of the largest tab because the previous
DataFrame stayed reachable through the for-loop scope until the
function returned.

If you add another long-running batch job that processes large
DataFrames in a loop, follow the same pattern.
