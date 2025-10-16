from typing import Any, Optional, cast

from src.database.db_manager import DBManager
from src.models.base import BaseModel
from src.utils.constants import DAILY_BONUS_XP


class User(BaseModel):
    table = 'users'
    pk = 'id'

    @classmethod
    def upsert_user(cls, user_id: int | str, display_name: str) -> dict[str, Any]:
        return cls.upsert(('id',), {'id': user_id, 'display_name': display_name})

    @classmethod
    def add_daily_bonus(cls, user_id: int | str, bonus: int = DAILY_BONUS_XP) -> None:
        with DBManager() as db:
            db.execute(
                'UPDATE users '
                'SET total_xp = total_xp + %s, updated_at = CURRENT_TIMESTAMP '
                'WHERE id = %s',
                (bonus, user_id),
            )

    @classmethod
    def get_profile(cls, user_id: int | str) -> Optional[dict[str, Any]]:
        with DBManager() as db:
            row = db.fetchone(
                'SELECT display_name, total_xp, level, updated_at '
                'FROM users WHERE id = %s',
                (user_id,),
            )
        return cast(Optional[dict[str, Any]], row)

    @classmethod
    def leaderboard_top(cls, limit: int) -> list[dict[str, Any]]:
        with DBManager() as db:
            rows = db.fetchall(
                'SELECT display_name, level, total_xp '
                'FROM users ORDER BY total_xp DESC LIMIT %s',
                (limit,),
            )
        return cast(list[dict[str, Any]], rows)
