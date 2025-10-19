import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Ensure consistent path regardless of where it's called from ---
# Get absolute path to the directory this script lives in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, 'migrations')

# Ensure src/ is on sys.path so relative imports work if needed
sys.path.append(os.path.dirname(BASE_DIR))


def create_migration(name: str):
    '''Create a new SQL migration file with a timestamp-based name.'''
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{timestamp}_{name.strip().lower().replace(" ", "_")}.py'
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    # Template for new migration files
    template = '''from src.database.db_manager import DBManager


def up(db_manager: DBManager):
    \'\'\'Apply this migration.\'\'\'
    pass


def down(db_manager: DBManager):
    \'\'\'Rollback this migration.\'\'\'
    pass
'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)

    logger.info(f'✅ Created new migration file: {filepath}')


if __name__ == '__main__':
    note = input('Enter a short note for this migration: ')
    create_migration(note)
