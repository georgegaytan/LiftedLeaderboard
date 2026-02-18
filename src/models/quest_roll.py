from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Json

from src.models.base import BaseModel


class QuestRoll(BaseModel):
    table = 'quest_rolls'
    pk = 'user_id'

    @classmethod
    def get_or_create(cls, user_id: int | str, activity_ids_func) -> dict[str, Any]:
        '''
        Get existing active roll or create a new one if expired/missing.
        activity_ids_func: Helper function to generate new activity IDs if needed.
        '''
        existing = cls.get(user_id)

        # Check if expired (older than 7 days)
        if existing:
            date_rolled = existing['date_rolled']
            if isinstance(date_rolled, str):
                date_rolled = datetime.fromisoformat(date_rolled)

            # Ensure timezone awareness
            if date_rolled.tzinfo is None:
                date_rolled = date_rolled.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            if now - date_rolled > timedelta(days=7):
                # Expired, roll new one
                new_ids = activity_ids_func()
                return cls.upsert(
                    ('user_id',),
                    {
                        'user_id': user_id,
                        'activity_ids': Json(new_ids),
                        'date_rolled': now,
                        'has_accepted': False,
                        'updated_at': now,
                    },
                )
            return existing

        # No existing roll, create one
        new_ids = activity_ids_func()
        now = datetime.now(timezone.utc)
        return cls.create(
            {
                'user_id': user_id,
                'activity_ids': Json(new_ids),
                'date_rolled': now,
                'has_accepted': False,
                'updated_at': now,
            }
        )

    @classmethod
    def mark_accepted(cls, user_id: int | str) -> None:
        cls.update(
            user_id, {'has_accepted': True, 'updated_at': datetime.now(timezone.utc)}
        )
