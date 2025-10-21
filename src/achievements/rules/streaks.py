from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.achievements.interface import AchievementRule
from src.achievements.registry import registry
from src.database.db_manager import DBManager


class BaseStreakAchievementRule(AchievementRule):
    code: str = ''
    name: str = ''
    description: str = ''

    period: str = 'day'  # day/week/month/year
    length: int = 7

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'name') and isinstance(cls.name, str):
            cls.name = f'Streak: {cls.name}'

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, ActivityRecordedEvent)

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        if not isinstance(event, ActivityRecordedEvent):
            return False, None
        if self.period == 'day':
            return self._check_daily_streak(event.user_id, event.date_occurred)
        elif self.period in ('week', 'month', 'year'):
            # Treat non-day periods as consecutive-day streaks using multipliers
            multipliers = {'week': 7, 'month': 31, 'year': 365}
            required = multipliers[self.period] * int(self.length or 0)
            return self._check_daily_streak(
                event.user_id, event.date_occurred, required_length=required
            )
        return False, None

    def _check_daily_streak(
        self, user_id: int | str, end_date: date, required_length: int | None = None
    ) -> tuple[bool, dict[str, Any] | None]:
        # Count back from end_date while each day has at least one record
        # Optimization: fetch a window of dates once, then scan in Python
        streak = 0
        req_len = (
            int(required_length)
            if required_length is not None
            else int(self.length or 0)
        )
        if req_len <= 0:
            return False, {'streak': streak, 'unit': 'day'}
        start_date = end_date - timedelta(days=req_len - 1)
        with DBManager() as db:
            rows = db.fetchall(
                '''
                SELECT DISTINCT date_occurred
                FROM activity_records
                WHERE user_id = %s AND date_occurred BETWEEN %s AND %s
                ''',
                (user_id, start_date, end_date),
            )
        dates_with_activity = {r['date_occurred'] for r in rows}
        cur = end_date
        while True:
            if cur not in dates_with_activity:
                break
            streak += 1
            if streak >= req_len:
                return True, {'streak': streak, 'unit': 'day'}
            cur = cur - timedelta(days=1)
        return False, {'streak': streak, 'unit': 'day'}


class DailyStreak1(BaseStreakAchievementRule):
    code = 'streak_day_1'
    name = 'Dailies'
    description = 'Recorded activities for 1 day.'
    period = 'day'
    length = 1
    xp_value = 50


class DailyStreak13(BaseStreakAchievementRule):
    code = 'streak_day_13'
    name = 'Lucky'
    description = 'Recorded activities for 10 consecutive days.'
    period = 'day'
    length = 7
    xp_value = 130


class DailyStreak42(BaseStreakAchievementRule):
    code = 'streak_day_42'
    name = 'The meaning of life'
    description = 'Recorded activities for 42 consecutive days.'
    period = 'day'
    length = 42
    xp_value = 420


class DailyStreak69(BaseStreakAchievementRule):
    code = 'streak_day_69'
    name = 'Nice'
    description = 'Recorded activities for 69 consecutive days.'
    period = 'day'
    length = 69
    xp_value = 690


class DailyStreak100(BaseStreakAchievementRule):
    code = 'streak_day_69'
    name = 'Century Club'
    description = 'Recorded activities for 100 consecutive days.'
    period = 'day'
    length = 100
    xp_value = 1000


class DailyStreak202(BaseStreakAchievementRule):
    code = 'streak_day_202'
    name = 'Inferior Scout Troop'
    description = 'Recorded activities for 202 consecutive days.'
    period = 'day'
    length = 202
    xp_value = 2020


class DailyStreak350(BaseStreakAchievementRule):
    code = 'streak_day_350'
    name = 'Tree Fiddy'
    description = 'Recorded activities for 350 consecutive days.'
    period = 'day'
    length = 350
    xp_value = 3500


class DailyStreak420(BaseStreakAchievementRule):
    code = 'streak_day_420'
    name = 'Ayy lmao'
    description = 'Recorded activities for 420 consecutive days.'
    period = 'day'
    length = 420
    xp_value = 42000


class WeeklyStreak1(BaseStreakAchievementRule):
    code = 'streak_week_1'
    name = 'Weeklies'
    description = 'Recorded activities for 1 week.'
    period = 'week'
    length = 1
    xp_value = 100


class WeeklyStreak2(BaseStreakAchievementRule):
    code = 'streak_week_2'
    name = '2 Week Notice'
    description = 'Recorded activities for 2 consecutive weeks.'
    period = 'week'
    length = 2
    xp_value = 200


class WeeklyStreak6(BaseStreakAchievementRule):
    code = 'streak_week_6'
    name = 'First 6-weeks'
    description = 'Recorded activities for 6 consecutive weeks.'
    period = 'week'
    length = 6
    xp_value = 600


class WeeklyStreak13(BaseStreakAchievementRule):
    code = 'streak_week_13'
    name = 'First Trimester'
    description = 'Recorded activities for 13 consecutive weeks.'
    period = 'week'
    length = 13
    xp_value = 1300


class WeeklyStreak27(BaseStreakAchievementRule):
    code = 'streak_week_27'
    name = 'Second Trimester'
    description = 'Recorded activities for 27 consecutive weeks.'
    period = 'week'
    length = 12
    xp_value = 2700


class WeeklyStreak40(BaseStreakAchievementRule):
    code = 'streak_week_40'
    name = 'Third Trimester'
    description = 'Recorded activities for 40 consecutive weeks.'
    period = 'week'
    length = 40
    xp_value = 4000


class MonthlyStreak1(BaseStreakAchievementRule):
    code = 'streak_month_1'
    name = 'Monthlies'
    description = 'Recorded activities for 1 consecutive months.'
    period = 'month'
    length = 1
    xp_value = 1000


class MonthlyStreak3(BaseStreakAchievementRule):
    code = 'streak_month_3'
    name = 'Quarterlies'
    description = 'Recorded activities for 3 consecutive months.'
    period = 'month'
    length = 3
    xp_value = 2000


class MonthlyStreak4(BaseStreakAchievementRule):
    code = 'streak_month_4'
    name = '"EARLY" 2023 Truther Part 2'
    description = 'Recorded activities for 4 consecutive months.'
    period = 'month'
    length = 4
    xp_value = 2023


class MonthlyStreak6(BaseStreakAchievementRule):
    code = 'streak_month_6'
    name = '"EARLY" 2023 Truther Part 3'
    description = 'Recorded activities for 6 consecutive months.'
    period = 'month'
    length = 6
    xp_value = 2023


class MonthlyStreak9(BaseStreakAchievementRule):
    code = 'streak_month_9'
    name = '"EARLY" 2023 Truther Finale'
    description = 'Recorded activities for 9 consecutive months.'
    period = 'month'
    length = 9
    xp_value = 2023


class MonthlyStreak13(BaseStreakAchievementRule):
    code = 'streak_month_13'
    name = 'Leap Month'
    description = 'Recorded activities for 13 consecutive months.'
    period = 'month'
    length = 13
    xp_value = 13130


class YearlyStreak1(BaseStreakAchievementRule):
    code = 'streak_year_1'
    name = 'Yearlies'
    description = 'Recorded activities for 1 year.'
    period = 'year'
    length = 1
    xp_value = 3650


class YearlyStreak2(BaseStreakAchievementRule):
    code = 'streak_year_2'
    name = 'Sophomore'
    description = 'Recorded activities for 2 consecutive years.'
    period = 'year'
    length = 2
    xp_value = 36500


class YearlyStreak3(BaseStreakAchievementRule):
    code = 'streak_year_3'
    name = 'Junior'
    description = 'Recorded activities for 3 consecutive years.'
    period = 'year'
    length = 3
    xp_value = 365000


class YearlyStreak4(BaseStreakAchievementRule):
    code = 'streak_year_4'
    name = 'Graduation'
    description = 'Recorded activities for 4 consecutive years.'
    period = 'year'
    length = 4
    xp_value = 3650000


# Daily Streaks
registry.register(DailyStreak1())
registry.register(DailyStreak13())
registry.register(DailyStreak42())
registry.register(DailyStreak69())
registry.register(DailyStreak100())
registry.register(DailyStreak202())
registry.register(DailyStreak350())
registry.register(DailyStreak420())

# Weekly Streaks
registry.register(WeeklyStreak1())
registry.register(WeeklyStreak2())
registry.register(WeeklyStreak6())
registry.register(WeeklyStreak13())
registry.register(WeeklyStreak27())
registry.register(WeeklyStreak40())

# Monthly Streaks
registry.register(MonthlyStreak1())
registry.register(MonthlyStreak3())
registry.register(MonthlyStreak4())
registry.register(MonthlyStreak6())
registry.register(MonthlyStreak9())
registry.register(MonthlyStreak13())

# Yearly Streaks
registry.register(YearlyStreak1())
registry.register(YearlyStreak2())
registry.register(YearlyStreak3())
registry.register(YearlyStreak4())
