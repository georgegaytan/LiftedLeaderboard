import os
import sqlite3
from typing import Iterable, Optional


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "wellness.db")

# TODO: Review Schema, potentially update for scalability? Also add created_at TIMESTAMP
# TODO: Can we optimize how we call ensure_db() on every function?
def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                total_xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                activity TEXT NOT NULL,
                xp_awarded INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def execute(query: str, params: Iterable | None = None):
    ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(query, tuple(params or ()))
        conn.commit()


def fetchall(query: str, params: Iterable | None = None) -> list[tuple]:
    ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(query, tuple(params or ()))
        return cur.fetchall()


def fetchone(query: str, params: Iterable | None = None) -> Optional[tuple]:
    rows = fetchall(query, params)
    return rows[0] if rows else None


