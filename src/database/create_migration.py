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
    template = (
        'from src.database.db_manager import DBManager\n'
        'import argparse\n'
        '\n'
        '\n'
        'def up(db_manager: DBManager):\n'
        '    # Apply this migration.\n'
        '    pass\n'
        '\n'
        '\n'
        'def down(db_manager: DBManager):\n'
        '    # Rollback this migration.\n'
        '    db_manager.execute(\n'
        '        \'DELETE FROM migrations\'\n'  # noqa: Q003
        f'        \'WHERE filename = \'{filename}\'\'\n'  # noqa: Q003
        '    )\n'
        '\n'
        '\n'
        'def main():\n'
        '    parser = argparse.ArgumentParser()\n'
        '    parser.add_argument('
        '        \'command\', choices=[\'up\', \'down\']'  # noqa: Q003
        '    )\n'
        '    args = parser.parse_args()\n'
        '\n'
        '    if args.command == \'up\':\n'  # noqa: Q003
        '        with DBManager() as _db:\n'
        '            up(_db)\n'
        '    elif args.command == \'down\':\n'  # noqa: Q003
        '        with DBManager() as _db:\n'
        '            down(_db)\n'
        '\n'
        '\n'
        'if __name__ == \'__main__\':\n'  # noqa: Q003
        '    main()\n'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)

    logger.info(f'✅ Created new migration file: {filepath}')


if __name__ == '__main__':
    note = input('Enter a short note for this migration: ')
    create_migration(note)
