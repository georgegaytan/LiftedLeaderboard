from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.models import activity as activity_module
from src.models import quest as quest_module


@pytest.fixture
def mock_db_manager(monkeypatch):
    mock_db = MagicMock()
    mock_manager = MagicMock()
    mock_manager.__enter__.return_value = mock_db
    mock_manager.__exit__.return_value = None

    # Patch DBManager in all necessary modules
    from src.models import base as base_module

    monkeypatch.setattr(quest_module, 'DBManager', lambda: mock_manager)
    monkeypatch.setattr(activity_module, 'DBManager', lambda: mock_manager)
    monkeypatch.setattr(base_module, 'DBManager', lambda: mock_manager)

    return mock_db


def test_quest_create(mock_db_manager):
    user_id = 123
    activity_id = 456
    deadline = datetime.now(timezone.utc) + timedelta(days=7)

    quest_module.Quest.create_new(user_id, activity_id, deadline, is_new_bonus=True)

    assert mock_db_manager.fetchall.called
    args, _ = mock_db_manager.fetchall.call_args
    sql = args[0]
    params = args[1]

    assert 'INSERT INTO user_quests' in sql or 'UPDATE' in sql
    assert params[0] == user_id  # params is a tuple in fetchall call from upsert
    # upsert params order depends on values.keys().
    # Let's just check if values are in params tuple.
    assert user_id in params
    assert activity_id in params
    assert True in params  # is_new_bonus


def test_quest_get_active(mock_db_manager):
    user_id = 123
    expected_row = {
        'id': 1,
        'user_id': user_id,
        'activity_id': 10,
        'deadline': datetime.now(timezone.utc),
        'is_new_bonus': False,
        'activity_name': 'Pushups',
        'activity_category': 'Strength',
        'xp_value': 10,
    }

    mock_db_manager.fetchone.return_value = expected_row

    result = quest_module.Quest.get_active(user_id)

    assert result == expected_row
    assert mock_db_manager.fetchone.called
    args, _ = mock_db_manager.fetchone.call_args
    assert args[1] == (user_id,)


def test_quest_delete(mock_db_manager):
    quest_id = 99
    quest_module.Quest.delete_quest(quest_id)

    assert mock_db_manager.execute.called
    args, _ = mock_db_manager.execute.call_args
    assert 'DELETE FROM user_quests' in args[0]
    assert args[1] == (quest_id,)


def test_activity_get_random(mock_db_manager):
    mock_rows = [
        {'id': 1, 'name': 'A1', 'category': 'C1', 'xp_value': 10},
        {'id': 2, 'name': 'A2', 'category': 'C1', 'xp_value': 20},
    ]
    mock_db_manager.fetchall.return_value = mock_rows

    result = activity_module.Activity.get_random(limit=2)

    assert len(result) == 2
    assert result == mock_rows
    assert mock_db_manager.fetchall.called
    assert 'ORDER BY RANDOM()' in mock_db_manager.fetchall.call_args[0][0]
