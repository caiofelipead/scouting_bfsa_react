"""
database.py — Neon PostgreSQL data layer for scouting data.
Stores WyScout, SkillCorner, Análises, and Oferecidos tables.
Uses the same DATABASE_URL as auth.py (Neon PostgreSQL).
"""

import os
import logging
from contextlib import contextmanager
from typing import Dict, Optional

import pandas as pd
import psycopg2
from psycopg2 import InterfaceError, OperationalError
from psycopg2.extras import execute_values
from psycopg2 import pool as pg_pool

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── Connection Pool ────────────────────────────────────────────────────
_pool: Optional[pg_pool.SimpleConnectionPool] = None


def _get_pg_url() -> str:
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _get_pool() -> pg_pool.SimpleConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        url = _get_pg_url()
        if not url:
            raise RuntimeError("DATABASE_URL not set — cannot connect to Neon PostgreSQL")
        _pool = pg_pool.SimpleConnectionPool(
            minconn=1, maxconn=5, dsn=url, connect_timeout=10,
        )
        logger.info("PostgreSQL connection pool created (min=1, max=5)")
    return _pool


def _is_dead(conn) -> bool:
    """Check whether a pooled connection is dead (server timed out, etc.).

    psycopg2's `conn.closed` flag flips only when WE explicitly close the
    connection — not when the server drops it. We probe with `SELECT 1` to
    detect the silent-death case which is what causes "connection already
    closed" errors after long idle periods on Neon/Render.
    """
    if conn is None:
        return True
    if getattr(conn, "closed", 0):
        return True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return False
    except (OperationalError, InterfaceError, psycopg2.Error):
        return True


def get_connection():
    """Return a healthy psycopg2 connection from the pool.

    Validates each checkout with a lightweight SELECT 1 and discards dead
    connections (server-side timeout, broken socket, etc.) before returning.
    Retries up to 3 times to ride out transient pool churn.
    """
    pool_obj = _get_pool()
    last_err: Optional[Exception] = None
    for _ in range(3):
        try:
            conn = pool_obj.getconn()
        except Exception as e:
            last_err = e
            continue
        if _is_dead(conn):
            try:
                pool_obj.putconn(conn, close=True)
            except Exception:
                pass
            continue
        try:
            conn.autocommit = False
        except Exception:
            pass
        return conn
    if last_err is not None:
        raise last_err
    raise OperationalError("Could not obtain a live PostgreSQL connection from the pool")


def release_connection(conn):
    """Return a connection to the pool, dropping it if it's dead."""
    if conn is None:
        return
    try:
        if not _pool or _pool.closed:
            try:
                conn.close()
            except Exception:
                pass
            return
        # Drop the conn instead of recycling if it's broken — otherwise the
        # next caller pulls a corpse and crashes with "connection already
        # closed".
        if getattr(conn, "closed", 0):
            _pool.putconn(conn, close=True)
            return
        _pool.putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def get_conn():
    """Context manager: leases a healthy connection and always returns it.

    On OperationalError/InterfaceError the connection is forcibly closed
    (rather than recycled) so the next caller doesn't pull a stale socket.
    """
    conn = get_connection()
    try:
        yield conn
    except (OperationalError, InterfaceError) as e:
        logger.error("Postgres connection error: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            if _pool and not _pool.closed:
                _pool.putconn(conn, close=True)
            else:
                conn.close()
        except Exception:
            pass
        conn = None  # signal finally to skip release
        raise
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if conn is not None:
            release_connection(conn)


# ── Schema ────────────────────────────────────────────────────────────

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS scouting_sheets (
    id SERIAL PRIMARY KEY,
    sheet_key TEXT NOT NULL UNIQUE,
    synced_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scouting_rows (
    id SERIAL PRIMARY KEY,
    sheet_key TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    data JSONB NOT NULL,
    UNIQUE (sheet_key, row_index)
);

CREATE INDEX IF NOT EXISTS idx_scouting_rows_sheet
    ON scouting_rows (sheet_key);

CREATE INDEX IF NOT EXISTS idx_scouting_rows_sheet_row
    ON scouting_rows (sheet_key, row_index);

CREATE INDEX IF NOT EXISTS idx_scouting_rows_data
    ON scouting_rows USING gin (data);
"""


def init_scouting_tables():
    """Create scouting tables if they don't exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_CREATE_TABLES_SQL)
        conn.commit()
        logger.info("Scouting tables initialized")
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


# ── Write (sync from Google Sheets) ──────────────────────────────────

def upsert_sheet_data(sheet_key: str, df: pd.DataFrame):
    """Replace all rows for a sheet_key with data from a DataFrame."""
    if df is None or len(df) == 0:
        logger.warning("Skipping upsert for '%s' — empty DataFrame", sheet_key)
        return 0

    # Deduplicate column names (append _2, _3, etc. for duplicates)
    cols = list(df.columns)
    seen = {}
    for i, c in enumerate(cols):
        if c in seen:
            seen[c] += 1
            cols[i] = f"{c}_{seen[c]}"
        else:
            seen[c] = 1
    df.columns = cols

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Delete old data for this sheet
            cur.execute("DELETE FROM scouting_rows WHERE sheet_key = %s", (sheet_key,))

            # Prepare rows as JSONB
            import json
            rows = []
            for i, (_, row) in enumerate(df.iterrows()):
                # Convert to dict, handling NaN → None
                row_dict = {}
                for col in df.columns:
                    val = row[col]
                    try:
                        is_na = pd.isna(val)
                    except (ValueError, TypeError):
                        is_na = False
                    if is_na:
                        row_dict[col] = None
                    else:
                        row_dict[col] = str(val) if not isinstance(val, (int, float)) else val
                rows.append((sheet_key, i, json.dumps(row_dict, ensure_ascii=False)))

            # Bulk insert
            execute_values(
                cur,
                "INSERT INTO scouting_rows (sheet_key, row_index, data) VALUES %s",
                rows,
                template="(%s, %s, %s::jsonb)",
                page_size=500,
            )

            # Update sync timestamp
            cur.execute("""
                INSERT INTO scouting_sheets (sheet_key, synced_at)
                VALUES (%s, NOW())
                ON CONFLICT (sheet_key)
                DO UPDATE SET synced_at = NOW()
            """, (sheet_key,))

        conn.commit()
        logger.info("Upserted %d rows for sheet '%s'", len(rows), sheet_key)
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


# ── Read (fast queries from Neon) ────────────────────────────────────

def load_sheet_dataframe(sheet_key: str) -> pd.DataFrame:
    """Load all rows for a sheet_key into a pandas DataFrame."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data FROM scouting_rows WHERE sheet_key = %s ORDER BY row_index",
                (sheet_key,),
            )
            rows = cur.fetchall()

        if not rows:
            logger.warning("No data found for sheet '%s'", sheet_key)
            return pd.DataFrame()

        data = [row[0] for row in rows]
        df = pd.DataFrame(data)
        logger.info("Loaded %d rows for sheet '%s' from PostgreSQL", len(df), sheet_key)
        return df
    finally:
        release_connection(conn)


def get_sync_status() -> Dict[str, Optional[str]]:
    """Return last sync timestamp for each sheet."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT sheet_key, synced_at FROM scouting_sheets")
            rows = cur.fetchall()
        return {row[0]: row[1].isoformat() if row[1] else None for row in rows}
    finally:
        release_connection(conn)


# ── VAEP / PlayeRank Tables ────────────────────────────────────────────

_CREATE_VAEP_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS vaep_ratings (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    player_name TEXT NOT NULL,
    team TEXT,
    league TEXT,
    position TEXT,
    competition_id INTEGER,
    season VARCHAR(10),
    minutes_played INTEGER DEFAULT 0,
    total_vaep FLOAT DEFAULT 0,
    vaep_per90 FLOAT DEFAULT 0,
    offensive_vaep FLOAT DEFAULT 0,
    defensive_vaep FLOAT DEFAULT 0,
    actions_count INTEGER DEFAULT 0,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vaep_ratings_player
    ON vaep_ratings (player_name);
CREATE INDEX IF NOT EXISTS idx_vaep_ratings_season
    ON vaep_ratings (season);
CREATE INDEX IF NOT EXISTS idx_vaep_ratings_position
    ON vaep_ratings (position);

CREATE TABLE IF NOT EXISTS vaep_actions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    player_name TEXT NOT NULL,
    match_id INTEGER,
    action_type VARCHAR(50),
    vaep_value FLOAT DEFAULT 0,
    offensive_value FLOAT DEFAULT 0,
    defensive_value FLOAT DEFAULT 0,
    x_start FLOAT,
    y_start FLOAT,
    x_end FLOAT,
    y_end FLOAT,
    minute INTEGER,
    second INTEGER,
    season VARCHAR(10),
    competition_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_vaep_actions_player
    ON vaep_actions (player_name);
CREATE INDEX IF NOT EXISTS idx_vaep_actions_match
    ON vaep_actions (match_id);

CREATE TABLE IF NOT EXISTS playerank_scores (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    player_name TEXT NOT NULL,
    team TEXT,
    league TEXT,
    position TEXT,
    season VARCHAR(10),
    role_cluster VARCHAR(50),
    composite_score FLOAT DEFAULT 0,
    scoring_dim FLOAT DEFAULT 0,
    playmaking_dim FLOAT DEFAULT 0,
    defending_dim FLOAT DEFAULT 0,
    physical_dim FLOAT DEFAULT 0,
    possession_dim FLOAT DEFAULT 0,
    percentile_in_cluster FLOAT DEFAULT 0,
    cluster_size INTEGER DEFAULT 0,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_playerank_player
    ON playerank_scores (player_name);
CREATE INDEX IF NOT EXISTS idx_playerank_cluster
    ON playerank_scores (role_cluster);
CREATE INDEX IF NOT EXISTS idx_playerank_season
    ON playerank_scores (season);
"""


_vaep_tables_initialized = False


def init_vaep_tables():
    """Create VAEP and PlayeRank tables if they don't exist (runs once)."""
    global _vaep_tables_initialized
    if _vaep_tables_initialized:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_CREATE_VAEP_TABLES_SQL)
        conn.commit()
        _vaep_tables_initialized = True
        logger.info("VAEP/PlayeRank tables initialized")
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def save_vaep_ratings(ratings: list, season: str, competition_id: int = None):
    """Save VAEP ratings to PostgreSQL, replacing existing for the same season."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Delete old ratings for this season (IS NOT DISTINCT FROM handles NULL)
            cur.execute(
                "DELETE FROM vaep_ratings WHERE season IS NOT DISTINCT FROM %s",
                (season,),
            )
            if ratings:
                execute_values(
                    cur,
                    """INSERT INTO vaep_ratings
                       (player_name, team, league, position, competition_id, season,
                        minutes_played, total_vaep, vaep_per90, offensive_vaep,
                        defensive_vaep, actions_count)
                       VALUES %s""",
                    [
                        (
                            r["player_name"], r.get("team"), r.get("league"),
                            r.get("position"), competition_id, season,
                            r.get("minutes_played", 0), r.get("total_vaep", 0),
                            r.get("vaep_per90", 0), r.get("offensive_vaep", 0),
                            r.get("defensive_vaep", 0), r.get("actions_count", 0),
                        )
                        for r in ratings
                    ],
                    page_size=200,
                )
        conn.commit()
        logger.info("Saved %d VAEP ratings for season %s", len(ratings), season)
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def save_vaep_actions(actions: list, season: str, competition_id: int = None):
    """Save individual VAEP action values to PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM vaep_actions WHERE season IS NOT DISTINCT FROM %s",
                (season,),
            )
            if actions:
                execute_values(
                    cur,
                    """INSERT INTO vaep_actions
                       (player_name, match_id, action_type, vaep_value,
                        offensive_value, defensive_value,
                        x_start, y_start, x_end, y_end,
                        minute, second, season, competition_id)
                       VALUES %s""",
                    [
                        (
                            a["player_name"], a.get("match_id"),
                            a.get("action_type"), a.get("vaep_value", 0),
                            a.get("offensive_value", 0), a.get("defensive_value", 0),
                            a.get("x_start"), a.get("y_start"),
                            a.get("x_end"), a.get("y_end"),
                            a.get("minute"), a.get("second"),
                            season, competition_id,
                        )
                        for a in actions
                    ],
                    page_size=500,
                )
        conn.commit()
        logger.info("Saved %d VAEP actions for season %s", len(actions), season)
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def save_playerank_scores(scores: list, season: str):
    """Save PlayeRank scores to PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM playerank_scores WHERE season IS NOT DISTINCT FROM %s",
                (season,),
            )
            if scores:
                execute_values(
                    cur,
                    """INSERT INTO playerank_scores
                       (player_name, team, league, position, season,
                        role_cluster, composite_score,
                        scoring_dim, playmaking_dim, defending_dim,
                        physical_dim, possession_dim,
                        percentile_in_cluster, cluster_size)
                       VALUES %s""",
                    [
                        (
                            s["player_name"], s.get("team"), s.get("league"),
                            s.get("position"), season,
                            s.get("role_cluster", "unknown"),
                            s.get("composite_score", 0),
                            s.get("scoring_dim", 0), s.get("playmaking_dim", 0),
                            s.get("defending_dim", 0), s.get("physical_dim", 0),
                            s.get("possession_dim", 0),
                            s.get("percentile_in_cluster", 0),
                            s.get("cluster_size", 0),
                        )
                        for s in scores
                    ],
                    page_size=200,
                )
        conn.commit()
        logger.info("Saved %d PlayeRank scores for season %s", len(scores), season)
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def load_vaep_ratings(season: str = None, position: str = None,
                      min_minutes: int = 0, league: str = None) -> pd.DataFrame:
    """Load VAEP ratings from PostgreSQL with optional filters."""
    conn = get_connection()
    try:
        query = "SELECT * FROM vaep_ratings WHERE 1=1"
        params = []
        if season:
            query += " AND season = %s"
            params.append(season)
        if position:
            query += " AND position = %s"
            params.append(position)
        if min_minutes > 0:
            query += " AND minutes_played >= %s"
            params.append(min_minutes)
        if league:
            query += " AND league = %s"
            params.append(league)
        query += " ORDER BY vaep_per90 DESC"
        df = pd.read_sql(query, conn, params=params)
        return df
    finally:
        release_connection(conn)


def load_vaep_player(player_name: str, season: str = None) -> dict:
    """Load VAEP rating for a specific player."""
    conn = get_connection()
    try:
        query = "SELECT * FROM vaep_ratings WHERE player_name = %s"
        params = [player_name]
        if season:
            query += " AND season = %s"
            params.append(season)
        query += " ORDER BY calculated_at DESC LIMIT 1"
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if not row:
                return {}
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
    finally:
        release_connection(conn)


def load_vaep_actions_for_player(player_name: str, season: str = None) -> pd.DataFrame:
    """Load VAEP actions for a specific player."""
    conn = get_connection()
    try:
        query = "SELECT * FROM vaep_actions WHERE player_name = %s"
        params = [player_name]
        if season:
            query += " AND season = %s"
            params.append(season)
        query += " ORDER BY match_id, minute, second"
        return pd.read_sql(query, conn, params=params)
    finally:
        release_connection(conn)


def load_playerank_scores_db(season: str = None, role_cluster: str = None,
                             dimension: str = None, league: str = None) -> pd.DataFrame:
    """Load PlayeRank scores from PostgreSQL with optional filters."""
    conn = get_connection()
    try:
        query = "SELECT * FROM playerank_scores WHERE 1=1"
        params = []
        if season:
            query += " AND season = %s"
            params.append(season)
        if role_cluster:
            query += " AND role_cluster = %s"
            params.append(role_cluster)
        if league:
            query += " AND league = %s"
            params.append(league)
        order_col = "composite_score"
        if dimension and dimension in ("scoring_dim", "playmaking_dim", "defending_dim",
                                        "physical_dim", "possession_dim"):
            order_col = dimension
        query += f" ORDER BY {order_col} DESC"
        return pd.read_sql(query, conn, params=params)
    finally:
        release_connection(conn)


def has_data() -> bool:
    """Check if there's any scouting data in the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM scouting_rows LIMIT 1)")
            return cur.fetchone()[0]
    except Exception:
        return False
    finally:
        release_connection(conn)


def get_data_age_hours() -> Optional[float]:
    """Return the age (in hours) of the oldest synced sheet, or None if no data."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXTRACT(EPOCH FROM (NOW() - MIN(synced_at))) / 3600.0 "
                "FROM scouting_sheets"
            )
            row = cur.fetchone()
            if row and row[0] is not None:
                return float(row[0])
            return None
    except Exception:
        return None
    finally:
        release_connection(conn)
