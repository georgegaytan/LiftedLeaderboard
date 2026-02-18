import asyncio
import logging
import pathlib
from datetime import date, datetime, timezone
from time import perf_counter
from typing import Literal, TypedDict, cast

import discord
import pendulum
from discord import Interaction, app_commands
from discord.ext import commands

from src.achievements.engine import engine
from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.components.activity_records import RecentRecordsView
from src.models.activity import Activity
from src.models.activity_record import ActivityRecord
from src.models.quest import Quest
from src.models.user import User
from src.utils.helper import level_to_rank

logger = logging.getLogger(__name__)


# =========================================================
# Caching
# =========================================================
class _CategoryCache(TypedDict):
    expires_at: float
    data: list[str]


class _ActivityCacheEntry(TypedDict):
    expires_at: float
    data: list[str]


_CACHE_TTL_SECONDS = 604800  # 1 week
_category_cache: _CategoryCache = {'expires_at': 0.0, 'data': []}
_activity_cache: dict[str, _ActivityCacheEntry] = {}
_activity_cache_warmed = False


async def _get_categories_cached(now: float) -> list[str]:
    if _category_cache['data'] and _category_cache['expires_at'] > now:
        return _category_cache['data']

    categories = await asyncio.to_thread(Activity.list_categories, active_only=True)
    _category_cache.update({'data': categories, 'expires_at': now + _CACHE_TTL_SECONDS})
    return categories


async def _get_activities_cached(category: str, now: float) -> list[str]:
    entry = _activity_cache.get(category)
    if entry and entry['expires_at'] > now:
        return entry['data']

    rows = await asyncio.to_thread(
        Activity.list_by_category, category, active_only=True
    )
    names = [a['name'] for a in rows]
    _activity_cache[category] = {'data': names, 'expires_at': now + _CACHE_TTL_SECONDS}
    return names


async def _warm_activity_cache_if_needed(now: float) -> None:
    global _activity_cache_warmed
    if _activity_cache_warmed:
        return

    categories = await _get_categories_cached(now)
    for cat in categories:
        try:
            await _get_activities_cached(cat, now)
        except Exception:
            logger.debug('Failed warming cache for category %s', cat)

    _activity_cache_warmed = True


# =========================================================
# Helpers
# =========================================================
def _parse_activity_date(date_input: str | None) -> date:
    '''
    Parse user-provided date string into a date object.
    '''
    if not date_input:
        return datetime.now(timezone.utc).date()

    cleaned = date_input.strip().lower()

    if cleaned == 'yesterday':
        return cast(date, pendulum.yesterday().date())

    try:
        return cast(date, pendulum.parse(cleaned, strict=False).date())
    except Exception as e:
        logger.debug('Date parse failed for "%s": %s', date_input, e)
        raise ValueError


def _format_achievement_lines(unlocked: list[dict]) -> list[str]:
    unique = {a.get('code'): a for a in unlocked}.values()
    lines = ['\n🏆 Achievements unlocked:']
    for a in unique:
        lines.append(
            f"- **{a.get('name', 'Achievement')}** "
            f"(+{int(a.get('xp_value', 0))} XP)\n"
            f"  _{a.get('description', '')}_"
        )
    return lines


def _level_audio_file(rank_changed: bool) -> pathlib.Path:
    base = pathlib.Path(__file__).resolve().parents[1]
    name = 'rank_up.ogg' if rank_changed else 'level_up.ogg'
    return base / 'assets' / 'audio' / name


# =========================================================
# Cogs
# =========================================================
class ActivityRecordsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- Autocomplete ----------------

    async def category_autocomplete(self, interaction: Interaction, current: str):
        now = perf_counter()
        categories = await _get_categories_cached(now)
        cur = (current or '').lower()
        return [
            app_commands.Choice(name=c, value=c) for c in categories if cur in c.lower()
        ]

    async def activity_autocomplete(self, interaction: Interaction, current: str):
        category = interaction.namespace.category
        if not category:
            return []

        now = perf_counter()
        await _warm_activity_cache_if_needed(now)
        names = await _get_activities_cached(category, now)

        cur = (current or '').lower()
        return [app_commands.Choice(name=n, value=n) for n in names if cur in n.lower()]

    # =========================================================

    # /record
    # =========================================================
    @app_commands.command(name='record', description='Record an activity to earn XP')
    @app_commands.autocomplete(
        category=category_autocomplete, activity=activity_autocomplete
    )
    async def record(
        self,
        interaction: Interaction,
        category: str,
        activity: str,
        note: str | None = None,
        date_occurred: str | None = None,
    ):
        user = interaction.user
        user_id = user.id
        display_name = user.display_name
        t0 = perf_counter()

        try:
            date_obj = _parse_activity_date(date_occurred)
        except ValueError:
            await interaction.response.send_message(
                '❌ Invalid date format. Try YYYY-MM-DD, MM/DD/YYYY, ' "or 'yesterday'",
                ephemeral=True,
            )
            return

        date_iso = date_obj.isoformat()
        today_iso = datetime.now(timezone.utc).date().isoformat()

        await asyncio.to_thread(User.upsert_user, user_id, display_name)

        before_profile = await asyncio.to_thread(User.get_profile, user_id)
        old_level = int(before_profile['level']) if before_profile else 1
        old_rank = level_to_rank(old_level)

        activity_row = await asyncio.to_thread(
            Activity.get_by_name_category, activity, category, active_only=True
        )
        if not activity_row:
            await interaction.response.send_message(
                f'❌ Activity "{activity}" not found in category "{category}".',
                ephemeral=True,
            )
            return

        xp_value = int(activity_row['xp_value'])
        activity_id = activity_row['id']

        # Duplicate validation
        activity_name = str(activity_row.get('name', activity))
        group_key = ActivityRecord._activity_group_key(category, activity_name)

        # Handle daily group activities (like Daily Steps)
        if group_key == 'steps_daily':
            dup = await asyncio.to_thread(
                ActivityRecord.has_group_activity_on_date,
                user_id,
                group_key,
                date_iso,
            )
            if dup:
                await interaction.response.send_message(
                    '❌ You already recorded a Daily Steps activity for that day.',
                    ephemeral=True,
                )
                return

        # Handle weekly group activities
        elif group_key in {
            'steps_weekly',
            'recovery_weekly_sleep',
            'diet_weekly_no_alcohol',
        }:
            # Check for weekly duplicates first
            weekly_dup = await asyncio.to_thread(
                ActivityRecord.has_group_activity_in_week,
                user_id,
                group_key,
                date_iso,
            )
            if weekly_dup:
                await interaction.response.send_message(
                    '❌ You already recorded a weekly version of that activity '
                    'in last 7 days.',
                    ephemeral=True,
                )
                return

            # Also check for same-day duplicates for weekly activities
            dup = await asyncio.to_thread(
                ActivityRecord.has_activity_on_date,
                user_id,
                activity_id,
                date_iso,
            )
            if dup:
                await interaction.response.send_message(
                    '❌ You already recorded that activity for that day.',
                    ephemeral=True,
                )
                return

        # Handle regular activities (no group key)
        else:
            dup = await asyncio.to_thread(
                ActivityRecord.has_activity_on_date,
                user_id,
                activity_id,
                date_iso,
            )
            if dup:
                await interaction.response.send_message(
                    '❌ You already recorded that activity for that day.',
                    ephemeral=True,
                )
                return

        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True)

        status_msg = await interaction.followup.send(
            '⏳ Recording your activity...', wait=True
        )

        # Daily bonus - check BEFORE inserting to see if this is first activity
        has_today = await asyncio.to_thread(
            ActivityRecord.has_record_on_date, user_id, today_iso
        )
        should_give_daily_bonus = not has_today

        await asyncio.to_thread(
            ActivityRecord.insert,
            user_id=user_id,
            activity_id=activity_id,
            note=note,
            date_occurred=date_iso,
            message_id=status_msg.id,
        )

        message_lines = [
            f'✅ Recorded: **{activity}** (+{xp_value} XP)',
            f'📂 Category: {category}',
        ]
        if note:
            message_lines.append(f'📝 _{note}_')
        if date_iso != today_iso:
            message_lines.append(f'📅 Date: {date_iso}')

        # Add daily bonus if this was the first activity of the day
        if should_give_daily_bonus:
            await asyncio.to_thread(User.add_daily_bonus, user_id)
            message_lines.append('🎁 Daily bonus: +10 XP')

        # Check for active quest completion
        active_quest = await asyncio.to_thread(Quest.get_active, user_id)
        if active_quest and active_quest['activity_id'] == activity_id:
            now = datetime.now(timezone.utc)
            if active_quest['deadline'] > now:
                # Quest completed!
                bonus_xp = 50 + (100 if active_quest['is_new_bonus'] else 0)
                await asyncio.to_thread(User.add_daily_bonus, user_id, bonus_xp)
                await asyncio.to_thread(Quest.delete_quest, active_quest['id'])

                quest_msg = f'⚔️ **Quest Completed!** (+{bonus_xp} XP)'
                if active_quest['is_new_bonus']:
                    quest_msg += ' (New Activity Bonus!)'
                message_lines.append(quest_msg)

                # We might want to trigger some event or sound?
                # For now, just the message and XP is good.
            else:
                # Expired quest
                await asyncio.to_thread(Quest.delete_quest, active_quest['id'])
                # message_lines.append(
                #     '⚠️ Your active quest for this activity has expired.'
                # )

        unlocked: list[dict] = []
        try:
            unlocked += engine.dispatch(
                ActivityRecordedEvent(
                    user_id=user_id,
                    activity_id=activity_id,
                    category=activity_row['category'],
                    date_occurred=date_obj,
                )
            )
        except Exception:
            logger.exception('ActivityRecordedEvent dispatch failed')

        after_profile = await asyncio.to_thread(User.get_profile, user_id)
        files: list[discord.File] = []

        if after_profile and 'level' in after_profile:
            new_level = int(after_profile['level'])
            new_rank = level_to_rank(new_level)

            if new_level > old_level:
                message_lines.append(f'🎉 Level up! Level {old_level} → {new_level}')

            if new_rank != old_rank:
                message_lines.append(f'🏅 Rank up! {old_rank} → {new_rank}')
                try:
                    unlocked += engine.dispatch(
                        RankChangedEvent(user_id=user_id, new_rank=new_rank)
                    )
                except Exception:
                    logger.exception('RankChangedEvent dispatch failed')

            if new_rank != old_rank or new_level > old_level:
                audio_path = _level_audio_file(new_rank != old_rank)
                if audio_path.exists():
                    files.append(
                        discord.File(str(audio_path), filename=audio_path.name)
                    )

        if unlocked:
            message_lines.extend(_format_achievement_lines(unlocked))

        logger.info(' /record completed in %.3fs', perf_counter() - t0)

        final_message = '\n'.join(message_lines)
        try:
            if files:
                await status_msg.edit(content=final_message, attachments=files)
            else:
                await status_msg.edit(content=final_message)
        except Exception:
            logger.exception('Failed editing message, sending fallback')
            if files:
                await interaction.followup.send(content=final_message, files=files)
            else:
                await interaction.followup.send(content=final_message)

    # =========================================================
    # /recent
    # =========================================================
    @app_commands.command(
        name='recent', description='View and edit your recent activity records'
    )
    async def recent(
        self,
        interaction: Interaction,
        limit: int = 5,
        sort_by: app_commands.Choice[str] | None = None,
    ):
        user_id = interaction.user.id
        lim = max(1, min(50, limit))
        sort_mode: Literal['occurred', 'created', 'updated'] = cast(
            Literal['occurred', 'created', 'updated'],
            (sort_by.value if sort_by else 'occurred').lower(),
        )

        rows = ActivityRecord.recent_for_user(
            user_id=user_id, limit=lim, sort=sort_mode
        )

        if not rows:
            await interaction.response.send_message(
                'No recent records found.', ephemeral=True
            )
            return

        title_map = {
            'occurred': 'Recently Occurred',
            'created': 'Recently Created',
            'updated': 'Recently Updated',
        }

        embed = discord.Embed(
            title=f'{title_map.get(sort_mode)} Activity Records '
            f'(showing {len(rows)})',
            color=discord.Color.blurple(),
        )

        for idx, r in enumerate(rows, start=1):
            label = f'{idx}. {r["activity_name"]} · {r["category"]}'
            details = f'📅 {r["date_occurred"]}  •  +{r["xp_value"]} XP'

            if r['note']:
                details += f'\n📝 {r["note"]}'

            embed.add_field(name=label, value=details, inline=False)

        view = RecentRecordsView(requestor_id=user_id, records=rows)

        if not interaction.response.is_done():
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityRecordsCog(bot))
