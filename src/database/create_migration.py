import os
from datetime import datetime

MIGRATIONS_DIR = os.path.join('migrations')
os.makedirs(MIGRATIONS_DIR, exist_ok=True)


def create_migration(_note: str):
    '''Create a new migration file with timestamp and note.'''
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Sanitize note to use in filename: lowercase, replace spaces with underscores
    note_safe = _note.strip().lower().replace(' ', '_')
    filename = f'{timestamp}_{note_safe}.py'
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    # Write template to the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'Migration for "{_note}"')

    print(f'✅ Created new migration file: {filepath}')


if __name__ == '__main__':
    note = input('Enter a short note for this migration: ')
    create_migration(note)
