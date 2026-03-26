"""
database.py — Neon PostgreSQL data layer for scouting data.
Stores WyScout, SkillCorner, Análises, and Oferecidos tables.
Uses the same DATABASE_URL as auth.py (Neon PostgreSQL).
"""

import os
import logging
from typing import Dict, Optional

import pandas as pd
import psycopg2
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
            minconn=2, maxconn=15, dsn=url, connect_timeout=10
        )
        logger.info("PostgreSQL connection pool created (min=2, max=15)")
    return _pool


def get_connection():
    """Return a psycopg2 connection from the pool."""
    conn = _get_pool().getconn()
    conn.autocommit = False
    return conn


def release_connection(conn):
    """Return a connection to the pool."""
    try:
        if _pool and not _pool.closed:
            _pool.putconn(conn)
    except Exception:
        pass


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
                    if pd.isna(val):
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
