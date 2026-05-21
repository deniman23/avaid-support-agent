from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


@contextmanager
def get_conn() -> Iterator[Any]:
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple | dict | None = None, limit: int | None = None) -> list[dict]:
    lim = limit or settings.max_rows
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchmany(lim)
            return [dict(r) for r in rows]


def fetch_one(sql: str, params: tuple | dict | None = None) -> dict | None:
    rows = fetch_all(sql, params, limit=1)
    return rows[0] if rows else None


def execute(sql: str, params: tuple | dict | None = None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql: str, params: tuple | dict | None = None) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
