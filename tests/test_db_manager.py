from src.services import db_manager

# TODO: Review test usefulness and add more
def test_db_bootstrap(tmp_path, monkeypatch):
    tmp_db = tmp_path / "wellness.db"
    monkeypatch.setenv("_DB_OVERRIDE", str(tmp_db))
    db_manager.ensure_db()
    # Tables should exist
    with db_manager.sqlite3.connect(db_manager.DB_PATH) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert {"users", "logs"}.issubset(tables)


