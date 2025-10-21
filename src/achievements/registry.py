from __future__ import annotations

from typing import Iterable, List

from src.achievements.interface import AchievementRule


class AchievementRegistry:
    def __init__(self) -> None:
        self._rules: List[AchievementRule] = []

    def register(self, rule: AchievementRule) -> None:
        # Avoid duplicates by code
        if not any(r.code == rule.code for r in self._rules):
            self._rules.append(rule)

    def all(self) -> Iterable[AchievementRule]:
        return list(self._rules)


registry = AchievementRegistry()
