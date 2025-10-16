'''
DB Migration: Populate activities table with default activities and XP
'''

from src.database.db_manager import DBManager

# List of activities: (category, name, xp_value)
ACTIVITIES = [
    # === Diet ===
    ('Diet', 'Daily Caloric Goal', 1),
    ('Diet', 'Daily Protein Goal', 1),
    ('Diet', 'Daily 5+ Servings of Fruit/Veg', 1),
    ('Diet', 'Week of no Alcohol', 3),
]


def up(db_manager: DBManager):
    # Insert activities into the DB
    for category, name, xp in ACTIVITIES:
        db_manager.execute(
            '''
            INSERT INTO activities (category, name, xp_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            ''',
            (category, name, xp),
        )

    print(f'✅ Populated {len(ACTIVITIES)} activities into the database.')


def down(db_manager: DBManager):
    pass
