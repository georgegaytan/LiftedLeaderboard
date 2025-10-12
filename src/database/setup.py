from src.database.schema import create_schema
from src.services import db_manager

# Step 1: Create database and tables
create_schema()
print('Database and tables created/verified.')

# Step 2: Optional: Verify tables exist
tables = db_manager.fetchall("SELECT name FROM sqlite_master WHERE type='table';")
print('Current tables in DB:', [t[0] for t in tables])
