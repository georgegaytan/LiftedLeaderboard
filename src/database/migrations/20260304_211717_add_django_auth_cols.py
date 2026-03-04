from src.database.db_manager import DBManager
import argparse


def up(db_manager: DBManager):
    # Apply this migration.
    db_manager.execute(
        'ALTER TABLE users '
        'ADD COLUMN IF NOT EXISTS email TEXT UNIQUE NULL, '
        'ADD COLUMN IF NOT EXISTS password TEXT NULL, '
        'ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE, '
        'ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE, '
        'ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ NULL;'
    )


def down(db_manager: DBManager):
    # Rollback this migration.
    db_manager.execute(
        'ALTER TABLE users '
        'DROP COLUMN IF EXISTS email, '
        'DROP COLUMN IF EXISTS password, '
        'DROP COLUMN IF EXISTS is_admin, '
        'DROP COLUMN IF EXISTS is_active, '
        'DROP COLUMN IF EXISTS last_login;'
    )
    db_manager.execute(
        'DELETE FROM migrations '
        "WHERE filename = '20260304_211717_add_django_auth_cols.py'"
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
