from src.utils.constants import RANKS


def level_to_rank(level: int) -> str:
    lvl = max(1, int(level))
    for th, name in RANKS:
        if lvl >= th:
            return name
    return RANKS[-1][1]
