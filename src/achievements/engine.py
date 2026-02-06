from __future__ import annotations

import src.achievements  # noqa: F401
from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.achievements.registry import registry
from src.models.achievement import Achievement
from src.models.user import User
from src.models.user_achievement import UserAchievement
from src.utils.helper import level_to_rank
from src.utils.tracing import trace_span


class AchievementsEngine:
    def dispatch(self, event: ActivityRecordedEvent | RankChangedEvent) -> list[dict]:
        with trace_span(
            'achievements.dispatch',
            {'event_type': type(event).__name__, 'user_id': event.user_id},
        ):
            earned_list: list[dict] = []
            for rule in registry.all():
                if not rule.handles(event):
                    continue

                with trace_span(
                    'achievements.rule_evaluation',
                    {'rule_code': rule.code, 'rule_name': rule.name},
                ):
                    try:
                        earned, metadata = rule.evaluate(event)
                    except Exception:
                        # Fail-safe: do not break recording flow
                        continue
                    if not earned:
                        continue

                    with trace_span(
                        'achievements.achievement_creation', {'rule_code': rule.code}
                    ):
                        # Persist if not already earned
                        ach = Achievement.get_one('code = %s', (rule.code,))
                        if not ach:
                            ach = Achievement.create(
                                {
                                    'code': rule.code,
                                    'name': rule.name,
                                    'description': rule.description,
                                    'is_active': True,
                                    'xp_value': getattr(rule, 'xp_value', 0),
                                }
                            )
                        # Capture pre-insert level/rank (for post-award comparison)
                        before_profile = User.get_profile(event.user_id)
                        old_level = (
                            int(before_profile['level'])
                            if before_profile and 'level' in before_profile
                            else 1
                        )
                        old_rank = level_to_rank(old_level)

                        if not UserAchievement.exists(
                            'user_id = %s AND achievement_id = %s',
                            (event.user_id, ach['id']),
                        ):
                            UserAchievement.create(
                                {
                                    'user_id': event.user_id,
                                    'achievement_id': ach['id'],
                                    'metadata': metadata or {},
                                }
                            )
                            earned_list.append(
                                {
                                    'code': ach.get('code'),
                                    'name': ach.get('name'),
                                    'description': ach.get('description'),
                                    'xp_value': int(ach.get('xp_value', 0)),
                                }
                            )

                            # Post-award: DB trigger may have increased xp & updated lvl
                            try:
                                after_profile = User.get_profile(event.user_id)
                                if after_profile and 'level' in after_profile:
                                    new_level = int(after_profile['level'])
                                    new_rank = level_to_rank(new_level)
                                    if old_rank != new_rank:
                                        chained = self.dispatch(
                                            RankChangedEvent(
                                                user_id=event.user_id,
                                                new_rank=new_rank,
                                            )
                                        )
                                        if chained:
                                            earned_list.extend(chained)
                            except Exception:
                                pass

            return earned_list


engine = AchievementsEngine()
