'''
DB Migration: Populate activities table with default activities and XP
'''

from src.services.db_manager import DBManager

# List of activities: (category, name, xp_value)
ACTIVITIES = [
    # === Steps ===
    ('Steps', '5000 steps in a day', 5),
    ('Steps', '10000 steps in a day', 10),
    ('Steps', '35000 steps in a week', 5),
    ('Steps', '70000 steps in a week', 10),
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
    ('Running', '60 min intense run', 15),
    # === Cycling ===
    ('Cycling', '30-60 min bike ride', 5),
    ('Cycling', '1-2 hour bike ride', 10),
    ('Cycling', '2-3 hour bike ride', 15),
    ('Cycling', '3+ hour bike ride', 20),
    # === Swimming ===
    ('Swimming', 'Swimming (20-40 min)', 10),
    ('Swimming', 'Swimming (1 hour+)', 15),
    # === Strength ===
    ('Strength', 'Gym weight session (30-60 min)', 10),
    ('Strength', 'Long gym session (90+ min)', 15),
    ('Strength', 'Bodyweight/Resistance Bands workout (20-40 min)', 5),
    ('Strength', 'Core or mobility session (15-30 min)', 3),
    # === Sports ===
    ('Sports', '1 hour low intensity sport', 5),
    ('Sports', '2 hours low intensity sport', 10),
    ('Sports', '3+ hours low intensity sport', 15),
    ('Sports', '1 hour high intensity sport', 8),
    ('Sports', '2 hours high intensity sport', 13),
    ('Sports', '3+ hours high intensity sport', 18),
    # === Recovery ===
    ('Recovery', 'Meditation (10-20 min)', 2),
    ('Recovery', 'Yoga (30-60 min)', 5),
    ('Recovery', 'Stretching or mobility (15-30 min)', 3),
    ('Recovery', 'A week of good sleep (8+ hours/day avg)', 10),
]


def up(db_manager: DBManager):
    # Insert activities into the DB
    for category, name, xp in ACTIVITIES:
        db_manager.execute(
            '''
            INSERT OR IGNORE INTO activities (category, name, xp_value)
            VALUES (?, ?, ?)
            ''',
            (category, name, xp),
        )

    print(f'✅ Populated {len(ACTIVITIES)} activities into the database.')
