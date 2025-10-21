from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from src.achievements.events import ActivityRecordedEvent, RankChangedEvent


@runtime_checkable
class AchievementRule(Protocol):
    code: str
    name: str
    description: str
    xp_value: int

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        pass

    def evaluate(
        self, event: ActivityRecordedEvent | RankChangedEvent
    ) -> tuple[bool, dict[str, Any] | None]:
        '''
        Return (earned, metadata). If earned is True and the user hasn't earned before,
        the engine will persist the achievement with optional metadata.
        '''
        pass
