from src.database.db_manager import DBManager


def up(db_manager: DBManager):
    # Create quest_rolls table
    db_manager.execute('''
        CREATE TABLE IF NOT EXISTS quest_rolls (
            user_id BIGINT PRIMARY KEY,
            activity_ids JSONB NOT NULL,
            date_rolled TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            has_accepted BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')


def down(db_manager: DBManager):
    db_manager.execute('DROP TABLE IF EXISTS quest_rolls')
    db_manager.execute(
        'DELETE FROM migrations '
        'WHERE filename = "20260218_230000_create_quest_rolls.py"'
    )
