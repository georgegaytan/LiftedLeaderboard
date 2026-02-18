from typing import Any, Optional, cast

from src.database.db_manager import DBManager
from src.models.base import BaseModel


class Activity(BaseModel):
    table = 'activities'

    @classmethod
    def list_categories(cls, active_only: bool = True, limit: int = 25) -> list[str]:
        where = 'WHERE is_archived = FALSE' if active_only else ''
        sql = (
            'SELECT DISTINCT category FROM activities '
            f'{where} ORDER BY category ASC LIMIT %s'
        )
        with DBManager() as db:
            rows = db.fetchall(sql, (limit,))
        return [r['category'] for r in rows]

    @classmethod
    def list_by_category(
        cls, category: str, active_only: bool = True, limit: int = 25
    ) -> list[dict[str, Any]]:
        where = 'AND is_archived = FALSE' if active_only else ''
        sql = (
            'SELECT id, name, xp_value, is_archived FROM activities '
            'WHERE category = %s '
            f'{where} '
            'ORDER BY name ASC LIMIT %s'
        )
        with DBManager() as db:
            rows = db.fetchall(sql, (category, limit))
        return cast(list[dict[str, Any]], rows)

    @classmethod
    def get_by_name_category(
        cls, name: str, category: str, active_only: bool = True
    ) -> Optional[dict[str, Any]]:
        where = 'AND is_archived = FALSE' if active_only else ''
        sql = (
            'SELECT id, name, category, xp_value, is_archived FROM activities '
            'WHERE name = %s AND category = %s '
            f'{where}'
        )
        with DBManager() as db:
            row = db.fetchone(sql, (name, category))
        return cast(Optional[dict[str, Any]], row)

    @classmethod
    def set_archived(cls, activity_id: int, is_archived: bool) -> None:
        with DBManager() as db:
            db.execute(
                'UPDATE activities SET is_archived = %s WHERE id = %s',
                (is_archived, activity_id),
            )

    @classmethod
    def upsert_activity(cls, name: str, category: str, xp_value: int) -> dict[str, Any]:
        return cls.upsert(
            ('name',),
            {
                'name': name,
                'category': category,
                'xp_value': xp_value,
            },
        )

    @classmethod
    def get_random(cls, limit: int = 5) -> list[dict[str, Any]]:
        sql = (
            'SELECT id, name, category, xp_value FROM activities '
            'WHERE is_archived = FALSE '
            'ORDER BY RANDOM() LIMIT %s'
        )
        with DBManager() as db:
            rows = db.fetchall(sql, (limit,))
        return cast(list[dict[str, Any]], rows)
