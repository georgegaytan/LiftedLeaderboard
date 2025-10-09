from services import db_manager

# Step 1: Create database and tables
db_manager.ensure_db()
print("Database and tables created/verified.")

# Step 2: Optional: Verify tables exist
tables = db_manager.fetchall("SELECT name FROM sqlite_master WHERE type='table';")
print("Current tables in DB:", [t[0] for t in tables])
