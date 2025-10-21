from typing import Any

from src.models.base import BaseModel


class Achievement(BaseModel):
    table = 'achievements'

    @classmethod
    def upsert_code(
        cls, code: str, name: str, description: str, xp_value: int = 0
    ) -> dict[str, Any]:
        return cls.upsert(
            ('code',),
            {
                'code': code,
                'name': name,
                'description': description,
                'is_active': True,
                'xp_value': int(xp_value),
            },
        )
