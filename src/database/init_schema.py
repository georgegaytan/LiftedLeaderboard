import logging
import os

from src.services.db_manager import DB_PATH, DBManager

logger = logging.getLogger(__name__)


# TODO POC: Move DB file into Google Drive or some cloud, on machine splits the data
def init_schema(db: DBManager):
    '''Create the database schema if it doesn't already exist.'''
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # --- USERS TABLE ---
    db.execute(
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
    db.execute(
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
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS activity_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            note TEXT DEFAULT NULL,
            date_occurred DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
        '''
    )

    # --- LEVEL THRESHOLDS TABLE ---
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS level_thresholds (
            level INTEGER PRIMARY KEY,
            xp_required INTEGER NOT NULL
        )
        '''
    )

    # --- MIGRATIONS TABLE ---
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    # --- INDEXES ---
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_activity_records_user_id '
        'ON activity_records(user_id);'
    )
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_activity_records_activity_id '
        'ON activity_records(activity_id);'
    )
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_activity_records_created_at '
        'ON activity_records(created_at);'
    )
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_activity_records_updated_at '
        'ON activity_records(updated_at);'
    )
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_activity_records_date_occurred '
        'ON activity_records(date_occurred);'
    )

    # --- TRIGGER: Automatically award XP when an activity record is created ---
    db.execute(
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

    # --- TRIGGER: Adjust XP when an activity record changes ---
    db.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS adjust_activity_xp_on_update
        AFTER UPDATE ON activity_records
        WHEN OLD.activity_id != NEW.activity_id
        BEGIN
            -- Subtract old XP value and add new XP value
            UPDATE users
            SET total_xp = total_xp
                - COALESCE(
                    (SELECT xp_value FROM activities WHERE id = OLD.activity_id), 0
                  )
                + COALESCE(
                    (SELECT xp_value FROM activities WHERE id = NEW.activity_id), 0
                  ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.user_id;
        END;
        '''
    )

    # --- TRIGGER: Revoke XP when an activity record is deleted ---
    db.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS revoke_activity_xp_on_delete
        AFTER DELETE ON activity_records
        BEGIN
            UPDATE users
            SET total_xp = total_xp - COALESCE(
                (SELECT xp_value FROM activities WHERE id = OLD.activity_id), 0
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.user_id;
        END;
        '''
    )

    # --- TRIGGER: Automatically update updated_at on user changes ---
    db.execute(
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
    db.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS update_activity_timestamp
        AFTER UPDATE ON activities
        BEGIN
            UPDATE activities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        '''
    )

    # --- TRIGGER: Automatically update updated_at on activity_record changes ---
    db.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS update_activity_record_timestamp
        AFTER UPDATE ON activity_records
        BEGIN
            UPDATE activity_records
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        '''
    )

    # --- TRIGGER: Auto-update level based on total XP ---
    db.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS update_user_level_on_xp_change
        AFTER UPDATE OF total_xp ON users
        BEGIN
            UPDATE users
            SET level = (
                SELECT MAX(level)
                FROM level_thresholds
                WHERE xp_required <= NEW.total_xp
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        '''
    )
