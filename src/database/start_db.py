import importlib.util
import os

from src.database.init_schema import init_schema
from src.services.db_manager import DBManager


def run(db: DBManager):
    '''Run full DB setup: schema + migrations.'''
    # Step 1: Create database and tables
    init_schema(db)
    print('Database and tables created/verified.')

    # Step 2: Optional: Verify tables exist
    tables = db.fetchall('SELECT name FROM sqlite_master WHERE type="table";')
    print('Current tables in DB:', [t['name'] for t in tables])

    # Step 3: Run migrations
    migrations_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'migrations'
    )
    if not os.path.exists(migrations_dir):
        print('No migrations directory found, skipping migrations.')
        return

    migration_files = sorted(
        f
        for f in os.listdir(migrations_dir)
        if f.endswith('.py') and not f.startswith('__')
    )
    applied_rows = db.fetchall('SELECT filename FROM migrations')
    applied_migrations = {row['filename'] for row in applied_rows}

    # Run only new migrations
    for filename in migration_files:
        if filename in applied_migrations:
            print(f'Skipping applied migration: {filename}')
            continue

        filepath = os.path.join(migrations_dir, filename)
        module_name = f'migration_{filename.replace(".py", "")}'

        try:
            # Dynamically import migration module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                raise ImportError(f'Could not load migration module: {filename}')

            migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration)

            if hasattr(migration, 'up'):
                print(f'Running migration: {filename}')
                migration.up(db)
                db.execute('INSERT INTO migrations (filename) VALUES (?)', (filename,))
            else:
                print(f'⚠️ Skipping {filename}: no `up()` function found.')

        except Exception as e:
            print(f'❌ Error running migration {filename}: {e}')
            raise

    print('Migrations complete.')


if __name__ == '__main__':
    with DBManager() as _db:
        run(_db)
