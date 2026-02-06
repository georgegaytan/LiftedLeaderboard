from datetime import date
from typing import Any, Literal, cast

from src.database.db_manager import DBManager
from src.models.base import BaseModel


class ActivityRecord(BaseModel):
    table = 'activity_records'

    @staticmethod
    def _activity_group_key(category: str, name: str) -> str | None:
        if category == 'Steps' and name.startswith('Daily Steps'):
            return 'steps_daily'
        if category == 'Steps' and name.startswith('Weekly Steps'):
            return 'steps_weekly'
        if category == 'Recovery' and name in (
            'A week of good sleep (7+ hours/day avg)',
            'A week of great sleep (8+ hours/day avg)',
        ):
            return 'recovery_weekly_sleep'
        if category == 'Diet' and name == 'Week of no Alcohol':
            return 'diet_weekly_no_alcohol'
        return None

    @classmethod
    def has_activity_on_date(
        cls,
        user_id: int | str,
        activity_id: int,
        date_iso: str,
        *,
        exclude_record_id: int | None = None,
    ) -> bool:
        sql = (
            'SELECT 1 FROM activity_records '
            'WHERE user_id = %s AND activity_id = %s AND date_occurred = %s'
        )
        params: list[Any] = [
            user_id,
            activity_id,
            date.fromisoformat(date_iso),
        ]
        if exclude_record_id is not None:
            sql += ' AND id <> %s'
            params.append(exclude_record_id)
        sql += ' LIMIT 1'

        with DBManager() as db:
            row = db.fetchone(sql, tuple(params))
        return row is not None

    @classmethod
    def has_group_activity_on_date(
        cls,
        user_id: int | str,
        group_key: str,
        date_iso: str,
        *,
        exclude_record_id: int | None = None,
    ) -> bool:
        if group_key == 'steps_daily':
            where = "a.category = 'Steps' AND a.name LIKE 'Daily Steps%%'"
        else:
            raise ValueError(f'Unknown daily group_key: {group_key}')

        sql = (
            'SELECT 1 FROM activity_records ar '
            'JOIN activities a ON a.id = ar.activity_id '
            f'WHERE ar.user_id = %s AND ar.date_occurred = %s AND {where}'
        )
        params: list[Any] = [user_id, date.fromisoformat(date_iso)]
        if exclude_record_id is not None:
            sql += ' AND ar.id <> %s'
            params.append(exclude_record_id)
        sql += ' LIMIT 1'

        with DBManager() as db:
            row = db.fetchone(sql, tuple(params))
        return row is not None

    @classmethod
    def has_group_activity_within_days(
        cls,
        user_id: int | str,
        group_key: str,
        date_iso: str,
        days: int,
        *,
        exclude_record_id: int | None = None,
    ) -> bool:
        if group_key == 'steps_weekly':
            where = "a.category = 'Steps' AND a.name LIKE 'Weekly Steps%%'"
        elif group_key == 'recovery_weekly_sleep':
            where = (
                "a.category = 'Recovery' AND a.name IN ("
                "'A week of good sleep (7+ hours/day avg)',"
                "'A week of great sleep (8+ hours/day avg)'"
                ')'
            )
        elif group_key == 'diet_weekly_no_alcohol':
            where = "a.category = 'Diet' AND a.name = 'Week of no Alcohol'"
        else:
            raise ValueError(f'Unknown weekly group_key: {group_key}')

        # Rolling window around date_iso, inclusive.
        sql = (
            'SELECT 1 FROM activity_records ar '
            'JOIN activities a ON a.id = ar.activity_id '
            f'WHERE ar.user_id = %s AND {where} '
            'AND ar.date_occurred >= (%s::date - (%s * INTERVAL \'1 day\')) '
            'AND ar.date_occurred <= (%s::date + (%s * INTERVAL \'1 day\'))'
        )
        params: list[Any] = [user_id, date_iso, days, date_iso, days]
        if exclude_record_id is not None:
            sql += ' AND ar.id <> %s'
            params.append(exclude_record_id)
        sql += ' LIMIT 1'

        with DBManager() as db:
            row = db.fetchone(sql, tuple(params))
        return row is not None

    @classmethod
    def insert(
        cls,
        user_id: int | str,
        activity_id: int,
        note: str | None,
        date_occurred: str,
        message_id: int | None = None,
    ) -> dict[str, Any]:
        return cls.create(
            {
                'user_id': user_id,
                'activity_id': activity_id,
                'note': note,
                'date_occurred': date_occurred,
                'message_id': message_id,
            }
        )

    @classmethod
    def has_record_on_date(cls, user_id: int | str, date_iso: str) -> bool:
        with DBManager() as db:
            row = db.fetchone(
                'SELECT 1 FROM activity_records '
                'WHERE user_id = %s AND created_at::date = %s LIMIT 1',
                (user_id, date.fromisoformat(date_iso)),
            )
        return row is not None

    @classmethod
    def recent_for_user(
        cls,
        user_id: int | str,
        limit: int,
        sort: Literal['occurred', 'created', 'updated'],
    ) -> list[dict[str, Any]]:
        if sort == 'created':
            order_clause = 'ORDER BY ar.created_at DESC, ar.id DESC'
        elif sort == 'updated':
            order_clause = 'ORDER BY ar.updated_at DESC, ar.id DESC'
        else:
            order_clause = 'ORDER BY ar.date_occurred DESC, ar.id DESC'
        sql = (
            'SELECT '
            'ar.id AS id, '
            'ar.note AS note, '
            'ar.date_occurred AS date_occurred, '
            'ar.created_at AS created_at, '
            'ar.updated_at AS updated_at, '
            'ar.message_id AS message_id, '
            'a.name AS activity_name, '
            'a.category AS category, '
            'a.xp_value AS xp_value '
            'FROM activity_records ar '
            'JOIN activities a ON a.id = ar.activity_id '
            'WHERE ar.user_id = %s AND a.is_archived = FALSE '
            f'{order_clause} LIMIT %s'
        )
        with DBManager() as db:
            rows = db.fetchall(sql, (user_id, limit))
        return cast(list[dict[str, Any]], rows)

    @classmethod
    def count_on_created_date(cls, user_id: int | str, date_iso: str) -> int:
        with DBManager() as db:
            row = db.fetchone(
                'SELECT COUNT(*) AS cnt FROM activity_records '
                'WHERE user_id = %s AND created_at::date = %s',
                (user_id, date.fromisoformat(date_iso)),
            )
        return int(row['cnt']) if row and 'cnt' in row else 0

    @classmethod
    def update_record(
        cls, record_id: int, activity_id: int, note: str | None, date_occurred: str
    ) -> dict[str, Any]:
        with DBManager() as db:
            rows = db.fetchall(
                'UPDATE activity_records '
                'SET activity_id = %s, note = %s, date_occurred = %s '
                'WHERE id = %s RETURNING *',
                (activity_id, note, date_occurred, record_id),
            )
        rows = cast(list[dict[str, Any]], rows)
        return cast(dict[str, Any], rows[0]) if rows else cast(dict[str, Any], {})

    @classmethod
    def delete_record(cls, record_id: int) -> None:
        with DBManager() as db:
            db.execute('DELETE FROM activity_records WHERE id = %s', (record_id,))
