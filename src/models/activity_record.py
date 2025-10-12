from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional


@dataclass
class ActivityRecord:
    user_id: int
    activity_id: int
    note: Optional[str] = None
    date_occurred: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int = field(init=False)  # Auto-assigned by DB
