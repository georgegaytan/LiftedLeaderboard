from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

EventType = Literal['activity_recorded', 'rank_changed']


@dataclass(frozen=True)
class ActivityRecordedEvent:
    user_id: int | str
    activity_id: int
    category: str
    date_occurred: date

    @property
    def type(self) -> EventType:
        return 'activity_recorded'


@dataclass(frozen=True)
class RankChangedEvent:
    user_id: int | str
    new_rank: str

    @property
    def type(self) -> EventType:
        return 'rank_changed'
