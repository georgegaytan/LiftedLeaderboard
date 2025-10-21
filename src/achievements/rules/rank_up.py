from __future__ import annotations

from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.achievements.interface import AchievementRule
from src.achievements.registry import registry
from src.utils.constants import RANKS as RANK_THRESHOLDS


class RankUpAchievementRule(AchievementRule):
    def __init__(self, rank_name: str) -> None:
        self.rank_name = rank_name
        self.code = f'rank_{rank_name.lower().replace(" ", "_")}'
        self.name = f'Rank: {rank_name}'
        self.description = f'Reached rank {rank_name}.'
        xp_by_rank = {
            'Bronze': 100,
            'Iron': 140,
            'Steel': 220,
            'Mithril': 3100,
            'Adamant': 4400,
            'Rune': 7000,
            'Dragon': 9300,
            'Demon': 10000,
            'God': 13200,
            'Max': 2277,
        }
        self.xp_value = xp_by_rank.get(rank_name, 50)

    def handles(self, event: ActivityRecordedEvent | RankChangedEvent) -> bool:
        return isinstance(event, RankChangedEvent)

    def evaluate(self, event: ActivityRecordedEvent | RankChangedEvent):
        if not isinstance(event, RankChangedEvent):
            return False, None
        return event.new_rank == self.rank_name, {'rank': event.new_rank}


# Generate rules based on configured ranks (name is second element)
for _, _rank_name in RANK_THRESHOLDS:
    registry.register(RankUpAchievementRule(_rank_name))
