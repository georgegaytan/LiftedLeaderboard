from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Activity:
    name: str
    category: str
    xp_value: int = 0
    is_archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(init=False)  # assigned after DB insert
