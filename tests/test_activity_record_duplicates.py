import pytest

from src.models import activity_record as activity_record_module
from src.models.activity_record import ActivityRecord


class _FakeDB:
    def __init__(self, row):
        self._row = row
        self.last_query = None
        self.last_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def fetchone(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return self._row


class _FakeDBManager:
    def __init__(self, row):
        self._row = row
        self.instance = None

    def __call__(self):
        self.instance = _FakeDB(self._row)
        return self.instance


def test_activity_group_key_steps_daily():
    assert (
        ActivityRecord._activity_group_key('Steps', 'Daily Steps 10k+') == 'steps_daily'
    )


def test_activity_group_key_steps_weekly():
    assert (
        ActivityRecord._activity_group_key('Steps', 'Weekly Steps 70k+') == 'steps_weekly'
    )


def test_activity_group_key_recovery_sleep_weekly():
    assert (
        ActivityRecord._activity_group_key(
            'Recovery', 'A week of good sleep (7+ hours/day avg)'
        )
        == 'recovery_weekly_sleep'
    )
    assert (
        ActivityRecord._activity_group_key(
            'Recovery', 'A week of great sleep (8+ hours/day avg)'
        )
        == 'recovery_weekly_sleep'
    )


def test_activity_group_key_diet_no_alcohol_weekly():
    assert (
        ActivityRecord._activity_group_key('Diet', 'Week of no Alcohol')
        == 'diet_weekly_no_alcohol'
    )


def test_has_activity_on_date_true(monkeypatch):
    fake_mgr = _FakeDBManager(row={'ok': 1})
    monkeypatch.setattr(activity_record_module, 'DBManager', fake_mgr)

    assert ActivityRecord.has_activity_on_date(1, 10, '2026-02-05') is True
    assert fake_mgr.instance is not None
    assert 'activity_id = %s' in (fake_mgr.instance.last_query or '')


def test_has_activity_on_date_false(monkeypatch):
    fake_mgr = _FakeDBManager(row=None)
    monkeypatch.setattr(activity_record_module, 'DBManager', fake_mgr)

    assert ActivityRecord.has_activity_on_date(1, 10, '2026-02-05') is False


def test_has_group_activity_on_date_unknown_key_raises():
    with pytest.raises(ValueError):
        ActivityRecord.has_group_activity_on_date(1, 'unknown', '2026-02-05')


def test_has_group_activity_within_days_unknown_key_raises():
    with pytest.raises(ValueError):
        ActivityRecord.has_group_activity_within_days(1, 'unknown', '2026-02-05', 7)


def test_has_group_activity_on_date_steps_daily(monkeypatch):
    fake_mgr = _FakeDBManager(row={'ok': 1})
    monkeypatch.setattr(activity_record_module, 'DBManager', fake_mgr)

    assert (
        ActivityRecord.has_group_activity_on_date(1, 'steps_daily', '2026-02-05')
        is True
    )
    assert fake_mgr.instance is not None
    q = fake_mgr.instance.last_query or ''
    assert "a.category = 'Steps'" in q
    assert "a.name LIKE 'Daily Steps%%'" in q


def test_has_group_activity_within_days_steps_weekly(monkeypatch):
    fake_mgr = _FakeDBManager(row={'ok': 1})
    monkeypatch.setattr(activity_record_module, 'DBManager', fake_mgr)

    assert (
        ActivityRecord.has_group_activity_within_days(
            1, 'steps_weekly', '2026-02-05', 7
        )
        is True
    )
    assert fake_mgr.instance is not None
    q = fake_mgr.instance.last_query or ''
    assert "a.name LIKE 'Weekly Steps%%'" in q
    assert "+ (%s * INTERVAL '1 day')" in q
