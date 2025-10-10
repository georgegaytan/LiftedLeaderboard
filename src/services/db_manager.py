import os
import sqlite3
import logging
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "wellness.db")

def ensure_db():
    """Initialize the database schema if it doesn't already exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")

        # --- USERS TABLE ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                display_name TEXT NOT NULL,
                total_xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- ACTIVITIES TABLE ---
        # Now includes XP value per activity
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                xp_value INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- LOGS TABLE ---
        # Logs link user -> activity; XP derived from activity.xp_value
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (activity_id) REFERENCES activities(id)
            )
        """)

        # --- INDEXES ---
        cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);")

        # --- TRIGGER: Automatically award XP based on activity.xp_value ---
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS award_activity_xp
            AFTER INSERT ON logs
            BEGIN
                UPDATE users
                SET total_xp = total_xp + (
                    SELECT xp_value FROM activities WHERE id = NEW.activity_id
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = NEW.user_id;
            END;
        """)

        conn.commit()

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


def fetchall(query: str, params: Iterable | None = None) -> list[sqlite3.Row]:
    """Fetch all rows from a SELECT query."""
    with get_connection() as conn:
        cur = conn.execute(query, tuple(params or ()))
        return cur.fetchall()


def fetchone(query: str, params: Iterable | None = None) -> Optional[sqlite3.Row]:
    """Fetch a single row from a SELECT query."""
    rows = fetchall(query, params)
    return rows[0] if rows else None
