from src.database.db_manager import DBManager


def up(db_manager: DBManager):
    # 1) Add column if it doesn't exist
    db_manager.execute(
        '''
        ALTER TABLE IF EXISTS users
        ADD COLUMN IF NOT EXISTS last_recorded_activity_date DATE
        '''
    )

    # 2) Backfill from existing activity_records
    db_manager.execute(
        '''
        UPDATE users u
        SET last_recorded_activity_date = sub.max_date
        FROM (
            SELECT user_id, MAX(date_occurred) AS max_date
            FROM activity_records
            GROUP BY user_id
        ) AS sub
        WHERE u.id = sub.user_id
        '''
    )


def down(db_manager: DBManager):
    db_manager.execute(
        '''
        ALTER TABLE IF EXISTS users
        DROP COLUMN IF EXISTS last_recorded_activity_date
        '''
    )
