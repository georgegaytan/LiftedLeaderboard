from datetime import datetime
from typing import Any, Optional, cast

from src.database.db_manager import DBManager
from src.models.base import BaseModel


class Quest(BaseModel):
    table = 'user_quests'

    @classmethod
    def create_new(
        cls,
        user_id: int | str,
        activity_id: int,
        deadline: datetime,
        is_new_bonus: bool = False,
    ) -> dict[str, Any]:
        return cls.upsert(
            ('id',),
            {
                'user_id': user_id,
                'activity_id': activity_id,
                'deadline': deadline,
                'is_new_bonus': is_new_bonus,
            },
        )

    @classmethod
    def get_active(cls, user_id: int | str) -> Optional[dict[str, Any]]:
        sql = (
            'SELECT uq.id, uq.user_id, uq.activity_id, uq.deadline, uq.is_new_bonus, '
            'a.name as activity_name, a.category as activity_category, a.xp_value '
            'FROM user_quests uq '
            'JOIN activities a ON uq.activity_id = a.id '
            'WHERE uq.user_id = %s '
            'ORDER BY uq.deadline ASC LIMIT 1'
        )
        with DBManager() as db:
            row = db.fetchone(sql, (user_id,))
        return cast(Optional[dict[str, Any]], row)

    @classmethod
    def delete_quest(cls, quest_id: int) -> None:
        with DBManager() as db:
            db.execute('DELETE FROM user_quests WHERE id = %s', (quest_id,))
