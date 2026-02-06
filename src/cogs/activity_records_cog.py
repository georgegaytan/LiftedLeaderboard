import logging
import pathlib
from datetime import date, datetime, timezone

import discord
import pendulum
from discord import Interaction, app_commands
from discord.ext import commands

from src.achievements.engine import engine
from src.achievements.events import ActivityRecordedEvent, RankChangedEvent
from src.components.activity_records import RecentRecordsView
from src.models.activity import Activity
from src.models.activity_record import ActivityRecord
from src.models.user import User
from src.utils.helper import level_to_rank
from src.utils.tracing import trace_span

logger = logging.getLogger(__name__)


class ActivityRecordsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Autocomplete for category
    async def category_autocomplete(self, interaction: Interaction, current: str):
        '''Autocomplete available categories from the DB.'''
        # Filter client-side after fetching limited categories
        categories = Activity.list_categories(active_only=True)
        cur = (current or '').lower()
        filtered = [c for c in categories if cur in c.lower()]
        return [app_commands.Choice(name=c, value=c) for c in filtered]

    # Autocomplete for activity based on selected category
    async def activity_autocomplete(self, interaction: Interaction, current: str):
        '''Autocomplete activity names within the selected category.'''
        # Check what category the user has currently selected
        category = interaction.namespace.category
        if not category:
            return []  # No category selected yet
        names = [
            a['name'] for a in Activity.list_by_category(category, active_only=True)
        ]
        cur = (current or '').lower()
        filtered = [n for n in names if cur in n.lower()]
        return [app_commands.Choice(name=n, value=n) for n in filtered]

    # Command: /record
    @app_commands.command(name='record', description='Record an activity to earn XP')
    @app_commands.describe(
        category='Activity category (e.g., Fitness, Learning)',
        activity='Specific activity name',
        note='Optional note about this activity',
        date_occurred='Date the activity occurred (default: today)',
    )
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
        '''Record an activity and automatically award XP.'''
        with trace_span(
            'discord.command',
            {
                'command': 'record',
                'user_id': interaction.user.id,
                'category': category,
                'activity': activity,
            },
        ):
            user_id = interaction.user.id
            display_name = interaction.user.display_name
            date_occurred = date_occurred or date.today().isoformat()

            try:
                with trace_span('record.date_parsing', {'date_input': date_occurred}):
                    date_obj = pendulum.parse(date_occurred, strict=False)
                    if not date_obj:
                        raise ValueError('Could not parse date')
                    date_obj = date_obj.date()  # Convert to date object for consistency
            except Exception as e:
                logger.debug(f'Failed to parse date "{date_occurred}": {e}')
                await interaction.response.send_message(
                    '❌ Invalid date format. '
                    'Try formats like: YYYY-MM-DD, MM/DD/YYYY, or "yesterday"',
                    ephemeral=True,
                )
                return

            # Ensure user exists
            with trace_span('record.user_upsert', {'user_id': user_id}):
                User.upsert_user(user_id, display_name)
            # Convert to ISO format string for consistency
            date_occurred_isoformat: str = date_obj.isoformat()

            # Capture pre-change level and rank
            with trace_span('record.profile_lookup', {'user_id': user_id}):
                before_profile = User.get_profile(user_id)
                old_level = int(before_profile['level']) if before_profile else 1
                old_rank = level_to_rank(old_level)

            # Daily bonus check (first record today)
            today_isoformat = datetime.now(timezone.utc).date().isoformat()
            with trace_span('record.daily_bonus_check', {'user_id': user_id}):
                check_bonus = not ActivityRecord.has_record_on_date(
                    user_id, today_isoformat
                )

            # Lookup activity
            with trace_span(
                'record.activity_lookup', {'activity': activity, 'category': category}
            ):
                activity_row = Activity.get_by_name_category(
                    activity, category, active_only=True
                )

            if not activity_row:
                await interaction.response.send_message(
                    f'❌ Activity "{activity}" not found in category "{category}".',
                    ephemeral=True,
                )
                return

            activity_id = activity_row['id']

            # Record the activity
            with trace_span('record.discord_response'):
                if not interaction.response.is_done():
                    await interaction.response.defer(thinking=True)

                # Send initial message and create record
                initial_message = await interaction.followup.send(
                    '⏳ Recording your activity...', wait=True
                )

            # Create the activity record
            with trace_span(
                'record.activity_insert',
                {'user_id': user_id, 'activity_id': activity_id, 'activity': activity},
            ):
                ActivityRecord.insert(
                    user_id=user_id,
                    activity_id=activity_id,
                    note=note,
                    date_occurred=date_occurred_isoformat,
                    message_id=initial_message.id,
                )

            # Build the success message
            message = f'✅ Recorded: **{activity}** (+{activity_row["xp_value"]} XP)'
            message += f'\n📂 Category: {category}'
            if note:
                message += f'\n📝 _{note}_'
            if date_occurred_isoformat != today_isoformat:
                message += f'\n📅 Date: {date_occurred_isoformat}'

            # Track achievements unlocked during this command
            unlocked: list[dict] = []

            # Apply daily bonus after successful record
            if check_bonus:
                with trace_span('record.daily_bonus_apply', {'user_id': user_id}):
                    User.add_daily_bonus(user_id)
                message += '\n🎁 Daily bonus: +10 XP'

            # Dispatch achievement event: activity recorded
            try:
                activity_category = activity_row['category']
                unlocked += engine.dispatch(
                    ActivityRecordedEvent(
                        user_id=user_id,
                        activity_id=activity_id,
                        category=activity_category,
                        date_occurred=date.fromisoformat(date_occurred_isoformat),
                    )
                )
            except Exception:
                pass

            # Capture post-change level and rank and append notifications
            after_profile = User.get_profile(user_id)
            files: list[discord.File] = []
            if after_profile and 'level' in after_profile:
                new_level = int(after_profile['level'])
                new_rank = level_to_rank(new_level)
                rank_changed = new_rank != old_rank
                level_changed = new_level > old_level

                if level_changed:
                    message += f'\n🎉 Level up! Level {old_level} → {new_level}'
                if rank_changed:
                    message += f'\n🏅 Rank up! {old_rank} → {new_rank}'

                    try:
                        unlocked += engine.dispatch(
                            RankChangedEvent(
                                user_id=user_id,
                                new_rank=new_rank,
                            )
                        )
                    except Exception as e:
                        logger.exception(f'Failed to dispatch level changed event: {e}')

                if rank_changed or level_changed:
                    base = pathlib.Path(__file__).resolve().parents[1]  # points to src/
                    audio_dir = base / 'assets' / 'audio'
                    audio_path = audio_dir / (
                        'rank_up.ogg' if rank_changed else 'level_up.ogg'
                    )
                    if audio_path.exists():
                        try:
                            files.append(
                                discord.File(str(audio_path), filename=audio_path.name)
                            )
                        except Exception:
                            pass  # Non-fatal: if file can't attach, still send message

            # Append unlocked achievements summary
            if unlocked:
                unique = {}
                for a in unlocked:
                    unique[a.get('code')] = a
                lines = [
                    f'- {a.get("name", "Achievement")} '
                    f'(+{int(a.get("xp_value", 0))} XP) \n'
                    f'- _{a.get("description", "Achievement Description")}_'
                    for a in unique.values()
                ]
                message += '\n\n🏆 Achievements unlocked:\n' + '\n'.join(lines)

            # Edit the initial message with the final content
            try:
                if files:
                    await initial_message.edit(content=message, files=files)
                else:
                    await initial_message.edit(content=message)
            except Exception as e:
                logger.error(f'Failed to edit message: {e}')
                # Fallback to sending a new message if editing fails
                if files:
                    await interaction.followup.send(content=message, files=files)
                else:
                    await interaction.followup.send(message)

    @app_commands.command(
        name='recent', description='View and edit your recent activity records'
    )
    @app_commands.describe(
        limit='How many records to show (default 5, max 50)',
        sort_by='How to sort records: '
        '"Date Occurred" (default), "Date Created", or "Date Updated"',
    )
    @app_commands.choices(
        sort_by=[
            app_commands.Choice(name='Recently Occurred', value='occurred'),
            app_commands.Choice(name='Recently Created', value='created'),
            app_commands.Choice(name='Recently Updated', value='updated'),
        ]
    )
    async def recent(
        self,
        interaction: Interaction,
        limit: int = 5,
        sort_by: app_commands.Choice[str] | None = None,
    ):
        user_id = interaction.user.id
        lim = max(1, min(50, limit or 5))
        sort_mode = (sort_by.value if sort_by else 'occurred').lower()
        rows = ActivityRecord.recent_for_user(
            user_id=user_id, limit=lim, sort=sort_mode  # type: ignore[arg-type]
        )

        if not rows:
            await interaction.response.send_message(
                'No recent records found.',
                ephemeral=True,
            )
            return

        title_map = {
            'occurred': 'Recently Occurred',
            'created': 'Recently Created',
            'updated': 'Recently Updated',
        }
        title_sort = title_map.get(sort_mode, 'Recently Occurred')

        embed = discord.Embed(
            title=f'{title_sort} Activity Records (showing {len(rows)})',
            color=discord.Color.blurple(),
        )

        for idx, r in enumerate(rows, start=1):
            label = f'{idx}. {r["activity_name"]} · {r["category"]}'

            details = f'📅 {r["date_occurred"]}  •  +{r["xp_value"]} XP'
            if sort_mode == 'updated' and r['updated_at']:
                details += f'\n🕓 Updated: {r["updated_at"]}'
            elif sort_mode == 'created' and r['created_at']:
                details += f'\n🕓 Created: {r["created_at"]}'

            if r['note']:
                details += f'\n📝 {r["note"]}'

            embed.add_field(name=label, value=details, inline=False)

        view = RecentRecordsView(requestor_id=user_id, records=rows)

        if interaction.message and interaction.message.reference:
            try:
                # Try to get the referenced message
                reference_message = await interaction.channel.fetch_message(
                    interaction.message.reference.message_id
                )
                if reference_message and reference_message.author == self.bot.user:
                    # Edit the referenced message if it's from the bot
                    await reference_message.edit(embed=embed, view=view)
                    await interaction.response.send_message(
                        '✅ Updated the activity record.', ephemeral=True, delete_after=5
                    )
                    return
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass  # Fall through to normal behavior

        # If not a reply or couldn't edit the referenced message, send a new one
        if not interaction.response.is_done():
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityRecordsCog(bot))
