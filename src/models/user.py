from dataclasses import dataclass


@dataclass
class User:
    user_id: str
    display_name: str
    total_xp: int = 0
    level: int = 1


