from dataclasses import dataclass
from datetime import datetime


@dataclass
class Log:
    id: int | None
    user_id: str
    activity: str
    xp_awarded: int
    created_at: datetime | None = None
