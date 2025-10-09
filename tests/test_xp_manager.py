from src.services import db_manager
from src.services.xp_manager import award_log_xp, top_users


# TODO: Review test usefulness and add more
def test_award_and_top(tmp_path, monkeypatch):
    # Route DB to temp
    tmp_db = tmp_path / "wellness.db"
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.setenv("_DB_OVERRIDE", str(tmp_db))
    # ensure_db uses module path; simple isolation by removing file if exists
    if tmp_db.exists():
        tmp_db.unlink()
    db_manager.ensure_db()

    res = award_log_xp("1", "Alice")
    assert res.xp > 0
    board = top_users(5)
    assert any(name == "Alice" for name, _ in board)


