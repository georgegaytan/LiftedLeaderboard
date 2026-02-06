from datetime import date

import pytest

import src.achievements.rules.streaks as streaks_module
from src.achievements.events import ActivityRecordedEvent, RankChangedEvent


def test_streak_rule_handles_only_activity_recorded():
    rule = streaks_module.DailyStreak7()
    assert rule.handles(ActivityRecordedEvent(1, 1, 'Steps', date.today())) is True
    assert rule.handles(RankChangedEvent(1, 'Bronze')) is False


def test_daily_streak_achieved(monkeypatch, fake_db):
    end = date(2026, 2, 7)
    fake_db.fetchall_results = [[
        {'date_occurred': date(2026, 2, 1)},
        {'date_occurred': date(2026, 2, 2)},
        {'date_occurred': date(2026, 2, 3)},
        {'date_occurred': date(2026, 2, 4)},
        {'date_occurred': date(2026, 2, 5)},
        {'date_occurred': date(2026, 2, 6)},
        {'date_occurred': date(2026, 2, 7)},
    ]]

    with pytest.MonkeyPatch.context() as mp:
        from tests.conftest import FakeDBManager

        mp.setattr(streaks_module, 'DBManager', FakeDBManager(fake_db))
        ok, meta = streaks_module.DailyStreak7().evaluate(
            ActivityRecordedEvent(1, 1, 'Steps', end)
        )

    assert ok is True
    assert meta is not None
    assert meta['streak'] >= 7


def test_daily_streak_not_achieved_gap(monkeypatch, fake_db):
    end = date(2026, 2, 7)
    fake_db.fetchall_results = [[
        {'date_occurred': date(2026, 2, 1)},
        {'date_occurred': date(2026, 2, 2)},
        {'date_occurred': date(2026, 2, 4)},
        {'date_occurred': date(2026, 2, 5)},
        {'date_occurred': date(2026, 2, 6)},
        {'date_occurred': date(2026, 2, 7)},
    ]]

    from tests.conftest import FakeDBManager

    monkeypatch.setattr(streaks_module, 'DBManager', FakeDBManager(fake_db))
    ok, meta = streaks_module.DailyStreak7().evaluate(
        ActivityRecordedEvent(1, 1, 'Steps', end)
    )
    assert ok is False
    assert meta is not None
    assert meta['streak'] < 7
