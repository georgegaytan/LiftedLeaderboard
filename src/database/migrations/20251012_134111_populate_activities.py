'''
DB Migration: Populate activities table with default activities and XP
'''

from src.database.db_manager import DBManager

# List of activities: (category, name, xp_value)
ACTIVITIES = [
    # === Steps ===
    ('Steps', 'Daily Steps 5k+ (pick only one per day)', 5),
    ('Steps', 'Daily Steps 10k+', 10),
    ('Steps', 'Daily Steps 15k+', 15),
    ('Steps', 'Daily Steps 20k+', 20),
    ('Steps', 'Weekly Steps 35k+ (pick only one per week)', 5),
    ('Steps', 'Weekly Steps 70k+', 10),
    ('Steps', 'Weekly Steps 105k+', 15),
    ('Steps', 'Daily Steps 140k+', 20),
    # === Hiking ===
    ('Hiking', '1 hour hiking', 3),
    ('Hiking', '2 hours hiking', 8),
    ('Hiking', '3+ hours hiking', 12),
    # === Running ===
    ('Running', '20 min jog', 3),
    ('Running', '40 min jog', 8),
    ('Running', '60 min jog', 12),
    ('Running', '90+ min jog', 15),
    ('Running', '20 min intense run', 5),
    ('Running', '40 min intense run', 10),
    ('Running', '60+ min intense run', 15),
    # === Cycling ===
    ('Cycling', 'Under 1 hour bike ride', 5),
    ('Cycling', '1-3 hour bike ride', 13),
    ('Cycling', '3+ hour bike ride', 20),
    # === Swimming ===
    ('Swimming', 'Casual Swimming (Under 30min actively swimming)', 10),
    ('Swimming', 'Intense Swimming (30+ min actively swimming)', 15),
    # === Strength ===
    ('Strength', 'Gym session (30-60 min)', 10),
    ('Strength', 'Long gym session (60+ min)', 15),
    ('Strength', 'Bodyweight/Resistance Bands workout', 5),
    ('Strength', 'Core or mobility session', 3),
    # === Sports ===
    ('Sports', '1 hour low intensity sport', 5),
    ('Sports', '2+ hours low intensity sport', 10),
    ('Sports', '1 hour high intensity sport', 8),
    ('Sports', '2+ hours high intensity sport', 13),
    # === Recovery ===
    ('Recovery', 'Meditation', 2),
    ('Recovery', 'Yoga', 5),
    ('Recovery', 'Stretching or massage session', 3),
    ('Recovery', 'A week of good sleep (7+ hours/day avg)', 5),
    ('Recovery', 'A week of great sleep (8+ hours/day avg)', 10),
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
