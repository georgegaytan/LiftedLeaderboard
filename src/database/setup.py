import importlib.util
import os

from src.database.schema import create_schema
from src.services.db_manager import DBManager


def run():
    '''Run full DB setup: schema + migrations.'''
    # Step 1: Create database and tables
    create_schema()
    print('Database and tables created/verified.')

    # Step 2: Optional: Verify tables exist
    with DBManager() as db:
        tables = db.fetchall('SELECT name FROM sqlite_master WHERE type="table";')
        print('Current tables in DB:', [t['name'] for t in tables])

        # Step 3: Run migrations
        MIGRATIONS_DIR = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'migrations'
        )
        if not os.path.exists(MIGRATIONS_DIR):
            print('No migrations directory found, skipping migrations.')
            return

        # Get all .py files in migrations folder, sorted by filename (timestamp)
        migration_files = sorted(
            f
            for f in os.listdir(MIGRATIONS_DIR)
            if f.endswith('.py') and not f.startswith('__')
        )

        for filename in migration_files:
            filepath = os.path.join(MIGRATIONS_DIR, filename)
            module_name = f'migration_{filename.replace(".py", "")}'

            # Dynamically import migration module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration)

            # Run the 'up' function
            print(f'Running migration: {filename}')
            migration.up(db)

    print('All migrations applied successfully.')


if __name__ == '__main__':
    run()
