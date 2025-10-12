import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'wellness.db'
)


# TODO POC: Move DB file into Google Drive or some cloud, on machine splits the data
def create_schema():
    '''Create the database schema if it doesn't already exist.'''
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('PRAGMA foreign_keys = ON;')

        # --- USERS TABLE ---
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                display_name TEXT NOT NULL,
                total_xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # --- ACTIVITIES TABLE ---
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                xp_value INTEGER NOT NULL DEFAULT 0,
                is_archived BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # --- ACTIVITY RECORDS TABLE ---
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS activity_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_id INTEGER NOT NULL,
                note TEXT DEFAULT NULL,
                date_occurred DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (activity_id) REFERENCES activities(id)
            )
            '''
        )

        # --- INDEXES ---
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_activity_records_user_id '
            'ON activity_records(user_id);'
        )
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_activity_records_activity_id '
            'ON activity_records(activity_id);'
        )
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_activity_records_created_at '
            'ON activity_records(created_at);'
        )

        # --- TRIGGER: Automatically award XP based on activity.xp_value ---
        cur.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS award_activity_xp
            AFTER INSERT ON activity_records
            BEGIN
                UPDATE users
                SET total_xp = total_xp + COALESCE(
                    (SELECT xp_value FROM activities WHERE id = NEW.activity_id), 0
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.user_id;
            END;
            '''
        )

        # --- TRIGGER: Automatically update updated_at on user changes ---
        cur.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS update_user_timestamp
            AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            '''
        )

        # --- TRIGGER: Automatically update updated_at on activity changes ---
        cur.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS update_activity_timestamp
            AFTER UPDATE ON activities
            BEGIN
                UPDATE activities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
            '''
        )

        conn.commit()
