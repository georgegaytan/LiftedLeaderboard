# Database Migrations

This folder contains database migration scripts for schema changes, data seeding, and other transformations. Migrations are applied automatically in timestamp order.

---

## Migration Naming Convention

Use the following naming pattern for migration files:

- `YYYYMMDD_HHMMSS_description.py`
- Example: `20251012_143210_add_initial_activities.py`

Notes:
- The timestamp ensures migrations are applied in chronological order.
- The description should be short, lowercase, and use underscores instead of spaces.

---

## Migration Structure

Each migration should contain:

- `up(db_manager)` – applies the migration (schema changes, inserts, updates, etc.)
- `down(db_manager)` – (OPTIONAL) rolls back the migration if needed
- A descriptive docstring explaining the purpose of the migration

---

## Creating a New Migration

You can create a new migration file using the migration scaffolding script:

```bash
python migration_create.py
```

It will prompt for a short note and generate a new timestamped Python file in the `/migrations` folder.

---

## Running Migrations

Migrations are run automatically by `src/database/setup_db.py`:

```python
from src.database import setup

setup.run()  # Creates schema and applies all migrations in /migrations
```

- This will create the database schema (if it doesn’t exist) and run all migrations in timestamp order.

### TODO POC: Track Migrations in a table to avoid rerunning applied migrations for idempotency
