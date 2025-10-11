import os
import sqlite3
import logging
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "wellness.db")

def get_connection() -> sqlite3.Connection:
    """Create a connection with foreign key enforcement and dict row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute(query: str, params: Iterable | None = None) -> None:
    """Execute a write operation (INSERT, UPDATE, DELETE)."""
    try:
        with get_connection() as conn:
            conn.execute(query, tuple(params or ()))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"SQLite execute() error: {e}\nQuery: {query}\nParams: {params}")
        raise


# TODO: Setup fetches to convert responses into Dataclasses/Classes from models
def fetchall(query: str, params: Iterable | None = None) -> list[sqlite3.Row]:
    """Fetch all rows from a SELECT query."""
    with get_connection() as conn:
        cur = conn.execute(query, tuple(params or ()))
        return cur.fetchall()


def fetchone(query: str, params: Iterable | None = None) -> Optional[sqlite3.Row]:
    """Fetch a single row from a SELECT query."""
    rows = fetchall(query, params)
    return rows[0] if rows else None
