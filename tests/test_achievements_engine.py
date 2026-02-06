from datetime import date

import src.achievements.engine as engine_module
from src.achievements.events import ActivityRecordedEvent


class _Rule:
    def __init__(self, code: str, earned: bool = True):
        self.code = code
        self.name = 'Rule'
        self.description = 'Desc'
        self.xp_value = 1
        self._earned = earned

    def handles(self, event):
        return True

    def evaluate(self, event):
        return self._earned, {'x': 1}


def test_engine_dispatch_creates_achievement_and_awards_once(
    monkeypatch, clean_registry
):
    rule = _Rule('r1', earned=True)
    clean_registry.register(rule)  # type: ignore[arg-type]

    monkeypatch.setattr(engine_module.Achievement, 'get_one', lambda *a, **k: None)
    monkeypatch.setattr(
        engine_module.Achievement,
        'create',
        lambda values: {
            'id': 123,
            'code': values['code'],
            'name': values['name'],
            'description': values['description'],
            'xp_value': values.get('xp_value', 0),
        },
    )

    exists_calls = {'n': 0}

    def _exists(*a, **k):
        exists_calls['n'] += 1
        return False

    monkeypatch.setattr(engine_module.UserAchievement, 'exists', _exists)

    created = []

    def _ua_create(values):
        created.append(values)
        return values

    monkeypatch.setattr(engine_module.UserAchievement, 'create', _ua_create)

    monkeypatch.setattr(engine_module.User, 'get_profile', lambda *a, **k: {'level': 1})

    earned = engine_module.engine.dispatch(
        ActivityRecordedEvent(
            user_id=1, activity_id=1, category='Steps', date_occurred=date(2026, 2, 5)
        )
    )

    assert len(earned) == 1
    assert earned[0]['code'] == 'r1'
    assert created and created[0]['achievement_id'] == 123
    assert exists_calls['n'] >= 1


def test_engine_dispatch_skips_if_not_earned(monkeypatch, clean_registry):
    rule = _Rule('r2', earned=False)
    clean_registry.register(rule)  # type: ignore[arg-type]

    monkeypatch.setattr(engine_module.Achievement, 'get_one', lambda *a, **k: None)
    monkeypatch.setattr(engine_module.UserAchievement, 'exists', lambda *a, **k: False)

    created = []
    monkeypatch.setattr(
        engine_module.UserAchievement, 'create', lambda v: created.append(v)
    )

    monkeypatch.setattr(engine_module.User, 'get_profile', lambda *a, **k: {'level': 1})

    earned = engine_module.engine.dispatch(
        ActivityRecordedEvent(
            user_id=1, activity_id=1, category='Steps', date_occurred=date(2026, 2, 5)
        )
    )

    assert earned == []
    assert created == []
