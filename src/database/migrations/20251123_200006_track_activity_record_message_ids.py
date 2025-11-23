from src.database.db_manager import DBManager
import argparse


def up(db_manager: DBManager):
    # Add message_id column to activity_records table
    db_manager.execute(
        'ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS message_id BIGINT'
    )


def down(db_manager: DBManager):
    db_manager.execute('ALTER TABLE activity_records DROP COLUMN IF EXISTS message_id')

    db_manager.execute(
        'DELETE FROM migrations '
        'WHERE filename = "20251123_200006_track_activity_record_message_ids.py"'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['up', 'down'])
    args = parser.parse_args()

    if args.command == 'up':
        with DBManager() as _db:
            up(_db)
    elif args.command == 'down':
        with DBManager() as _db:
            down(_db)


if __name__ == '__main__':
    main()
