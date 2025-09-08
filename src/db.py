import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "urlshort.db"))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

_CONNECTION = None

def connection() -> sqlite3.Connection:
    global _CONNECTION
    if _CONNECTION is None:
        _CONNECTION = get_connection()
    return _CONNECTION

@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def create_tables():
    with tx() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                long_url TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                ts TEXT NOT NULL,
                user_agent TEXT,
                ip TEXT,
                city TEXT,
                FOREIGN KEY(code) REFERENCES urls(code)
            );
            """
        )


def insert_url(code: str, long_url: str, created_at: str):
    with tx() as conn:
        conn.execute(
            "INSERT INTO urls(code, long_url, created_at) VALUES (?, ?, ?)",
            (code, long_url, created_at),
        )


def get_url(code: str):
    with tx() as conn:
        cur = conn.execute("SELECT * FROM urls WHERE code = ?", (code,))
        return cur.fetchone()


def code_exists(code: str) -> bool:
    with tx() as conn:
        cur = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,))
        return cur.fetchone() is not None


def insert_visit(code: str, ts: str, user_agent: str | None, ip: str | None, city: str | None):
    with tx() as conn:
        conn.execute(
            "INSERT INTO visits(code, ts, user_agent, ip, city) VALUES (?, ?, ?, ?, ?)",
            (code, ts, user_agent, ip, city),
        )


def visit_stats(code: str, limit: int = 20):
    with tx() as conn:
        total = conn.execute("SELECT COUNT(*) FROM visits WHERE code = ?", (code,)).fetchone()[0]
        last = conn.execute("SELECT MAX(ts) FROM visits WHERE code = ?", (code,)).fetchone()[0]
        cur = conn.execute(
            "SELECT ts, user_agent, ip, city FROM visits WHERE code = ? ORDER BY id DESC LIMIT ?",
            (code, limit),
        )
        recent = [dict(row) for row in cur.fetchall()]
        return {"total": total, "last_access": last, "recent": recent}
