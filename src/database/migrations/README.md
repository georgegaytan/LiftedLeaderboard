# Database Migrations

This folder contains database migration scripts for schema changes and data transformations.

## Migration Naming Convention

Use the following naming pattern for migration files:
- `YYYY_MM_DD_HHMMSS_description.py`
- Example: `2024_01_15_143022_add_user_preferences.py`

## Migration Structure

Each migration should contain:
- `up()` function - applies the migration
- `down()` function - rolls back the migration
- Descriptive docstring explaining the changes

## Example Migration

```python
def up():
    """Add user preferences table"""
    # Migration code here
    pass

def down():
    """Remove user preferences table"""
    # Rollback code here
    pass
```

## Running Migrations

Migrations can be run using a migration runner (to be implemented).
