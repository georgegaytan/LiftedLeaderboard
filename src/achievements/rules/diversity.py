from __future__ import annotations

from typing import Any

from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.achievements.interface import AchievementRule
from src.achievements.registry import registry
from src.database.db_manager import DBManager


class BaseDiverseActivitiesAchievementRule(AchievementRule):
    '''Base rule for distinct activity achievements'''

    required_count: int = 0  # to be overridden in subclasses

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'name') and isinstance(cls.name, str):
            cls.name = f'Diversity: {cls.name}'

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, ActivityRecordedEvent)

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        if not isinstance(event, ActivityRecordedEvent):
            return False, None

        with DBManager() as db:
            row = db.fetchone(
                '''
                SELECT COUNT(DISTINCT ar.activity_id) AS cnt
                FROM activity_records ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.user_id = %s
                  AND (a.is_archived = FALSE OR a.is_archived IS NULL)
                ''',
                (event.user_id,),
            )

        cnt = int(row['cnt']) if row and 'cnt' in row else 0
        return cnt >= self.required_count, {'distinct_activities': cnt}


class DistinctActivities10(BaseDiverseActivitiesAchievementRule):
    code = 'diverse_activities_10'
    name = 'Active Andy'
    description = 'Recorded 10 different activities.'
    xp_value = 500
    required_count = 10


class DistinctActivities20(BaseDiverseActivitiesAchievementRule):
    code = 'diverse_activities_20'
    name = 'Active Anderson'
    description = 'Recorded 20 different activities.'
    xp_value = 1000
    required_count = 20


class DistinctActivities30(BaseDiverseActivitiesAchievementRule):
    code = 'diverse_activities_30'
    name = 'Active Mister Anderson'
    description = 'Recorded 30 different activities.'
    xp_value = 2000
    required_count = 30


class AllActivitiesAchievementRule(AchievementRule):
    code = 'diverse_activities_all'
    name = 'Diversity: Active Miss Anderson'
    description = 'Recorded all different activities.'
    xp_value = 2500

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, ActivityRecordedEvent)

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        if not isinstance(event, ActivityRecordedEvent):
            return False, None

        with DBManager() as db:
            # Count how many *distinct non-archived* activities the user has recorded
            user_row = db.fetchone(
                '''
                SELECT COUNT(DISTINCT ar.activity_id) AS user_count
                FROM activity_records ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.user_id = %s AND a.is_archived = FALSE
                ''',
                (event.user_id,),
            )

            # Count total *non-archived* activities available
            total_row = db.fetchone(
                'SELECT COUNT(*) AS total_count FROM activities '
                'WHERE is_archived = FALSE'
            )

        user_count = (
            int(user_row['user_count']) if user_row and 'user_count' in user_row else 0
        )
        total_count = (
            int(total_row['total_count'])
            if total_row and 'total_count' in total_row
            else 0
        )

        achieved = user_count == total_count and total_count > 0

        return (
            achieved,
            {
                'user_distinct_activities': user_count,
                'total_activities': total_count,
            },
        )


class FiveCategoriesAchievementRule(AchievementRule):
    code = 'diverse_categories_5'
    name = 'Diversity: Cross-Trainer'
    description = 'Recorded activities across 5 different categories.'
    xp_value = 500

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, ActivityRecordedEvent)

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        if not isinstance(event, ActivityRecordedEvent):
            return False, None
        with DBManager() as db:
            row = db.fetchone(
                '''
                SELECT COUNT(DISTINCT a.category) AS cnt
                FROM activity_records ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.user_id = %s
                ''',
                (event.user_id,),
            )
        cnt = int(row['cnt']) if row and 'cnt' in row else 0
        return cnt >= 5, {'distinct_categories': cnt}


class AllCategoriesAchievementRule(AchievementRule):
    code = 'diverse_categories_all'
    name = 'Diversity: Diversity-Trainer'
    description = 'Recorded activities across all available categories.'
    xp_value = 500

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, ActivityRecordedEvent)

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        if not isinstance(event, ActivityRecordedEvent):
            return (False, None)

        with DBManager() as db:
            # Count how many distinct categories the user has recorded
            user_row = db.fetchone(
                '''
                SELECT COUNT(DISTINCT a.category) AS user_count
                FROM activity_records ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.user_id = %s
                ''',
                (event.user_id,),
            )

            # Count how many total distinct categories exist
            total_row = db.fetchone(
                'SELECT COUNT(DISTINCT category) AS total_count FROM activities'
            )

        user_count = (
            int(user_row['user_count']) if user_row and 'user_count' in user_row else 0
        )
        total_count = (
            int(total_row['total_count'])
            if total_row and 'total_count' in total_row
            else 0
        )

        achieved = user_count == total_count and total_count > 0

        return achieved, {
            'user_distinct_categories': user_count,
            'total_categories': total_count,
        }


registry.register(DistinctActivities10())
registry.register(DistinctActivities20())
registry.register(DistinctActivities30())
registry.register(AllActivitiesAchievementRule())
registry.register(FiveCategoriesAchievementRule())
registry.register(AllCategoriesAchievementRule())
