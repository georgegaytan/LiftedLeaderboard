from dataclasses import dataclass
from . import db_manager
from ..utils.constants import BASE_XP_PER_LOG


@dataclass(frozen=True)
class XpAward:
    xp: int
    reason: str

# TODO: Review XP management philosophy and make this scalable
def award_log_xp(user_id: str, display_name: str, multiplier: float = 1.0) -> XpAward:
    xp = max(1, int(BASE_XP_PER_LOG * multiplier))
    db_manager.execute(
        "INSERT OR IGNORE INTO users(user_id, display_name) VALUES (?, ?)",
        (user_id, display_name),
    )
    db_manager.execute(
        "UPDATE users SET total_xp = total_xp + ?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
        (xp, user_id),
    )
    db_manager.execute(
        "INSERT INTO logs(user_id, activity, xp_awarded) VALUES(?, ?, ?)",
        (user_id, "wellness_log", xp),
    )
    return XpAward(xp=xp, reason="wellness_log")


def top_users(limit: int = 10) -> list[tuple[str, int]]:
    rows = db_manager.fetchall(
        "SELECT display_name, total_xp FROM users ORDER BY total_xp DESC LIMIT ?",
        (limit,),
    )
    return [(name or "Unknown", xp) for name, xp in rows]


