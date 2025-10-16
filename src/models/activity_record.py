from typing import Any, Literal, cast

from src.database.db_manager import DBManager
from src.models.base import BaseModel


class ActivityRecord(BaseModel):
    table = 'activity_records'

    @classmethod
    def insert(
        cls,
        user_id: int | str,
        activity_id: int,
        note: str | None,
        date_occurred: str,
    ) -> dict[str, Any]:
        return cls.create(
            {
                'user_id': user_id,
                'activity_id': activity_id,
                'note': note,
                'date_occurred': date_occurred,
            }
        )

    @classmethod
    def has_record_on_date(cls, user_id: int | str, date_iso: str) -> bool:
        with DBManager() as db:
            row = db.fetchone(
                'SELECT 1 FROM activity_records '
                'WHERE user_id = %s AND date_occurred = %s LIMIT 1',
                (user_id, date_iso),
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
            'SELECT ar.id AS id, ar.note AS note, ar.date_occurred AS date_occurred, '
            'ar.created_at AS created_at, ar.updated_at AS updated_at, '
            'a.name AS activity_name, a.category AS category, a.xp_value AS xp_value '
            'FROM activity_records ar '
            'JOIN activities a ON a.id = ar.activity_id '
            'WHERE ar.user_id = %s AND a.is_archived = FALSE '
            f'{order_clause} LIMIT %s'
        )
        with DBManager() as db:
            rows = db.fetchall(sql, (user_id, limit))
        return cast(list[dict[str, Any]], rows)

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
