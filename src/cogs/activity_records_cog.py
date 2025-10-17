import logging
from datetime import date, datetime, timezone
from time import perf_counter

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from src.components.activity_records import RecentRecordsView
from src.models.activity import Activity
from src.models.activity_record import ActivityRecord
from src.models.user import User

logger = logging.getLogger(__name__)


class ActivityRecordsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete for category ---
    async def category_autocomplete(self, interaction: Interaction, current: str):
        '''Autocomplete available categories from the DB.'''
        # Filter client-side after fetching limited categories
        categories = Activity.list_categories(active_only=True)
        cur = (current or '').lower()
        filtered = [c for c in categories if cur in c.lower()]
        return [app_commands.Choice(name=c, value=c) for c in filtered]

    # --- Autocomplete for activity based on selected category ---
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

    # --- Command: /record ---
    @app_commands.command(name='record', description='Record an activity to earn XP')
    @app_commands.describe(
        category='Choose the category of activity (e.g., Running, Swimming, etc.)',
        activity='Select the specific activity',
        note='Optional note about your session',
        date_occurred='When the activity occurred in YYYY-MM-DD (default: today)',
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
        user_id = interaction.user.id
        display_name = interaction.user.display_name
        date_value = date_occurred or date.today().isoformat()
        t0 = perf_counter()

        try:
            date_obj = date.fromisoformat(date_value)
        except ValueError:
            await interaction.response.send_message(
                '❌ Invalid date format. Use YYYY-MM-DD.', ephemeral=True
            )
            return

        # Ensure user exists
        User.upsert_user(user_id, display_name)
        # Optionally convert back to string to normalize
        date_value = date_obj.isoformat()

        # --- Daily bonus check (first record today) ---
        check_bonus = False
        today_str = datetime.now(timezone.utc).date().isoformat()
        if date_value == today_str:
            check_bonus = not ActivityRecord.has_record_on_date(user_id, today_str)

        # --- Lookup activity ---
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

        # --- Record the activity ---
        t_before_insert = perf_counter()
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True, ephemeral=True)
        ActivityRecord.insert(
            user_id=user_id,
            activity_id=activity_id,
            note=note,
            date_occurred=date_value,
        )
        t_after_insert = perf_counter()

        # XP is handled automatically by trigger
        message = f"✅ Recorded: **{activity}** (+{activity_row['xp_value']} XP)"
        message += f'\n📂 Category: {category}'
        if note:
            message += f'\n📝 _{note}_'
        if date_occurred:
            message += f'\n📅 Date: {date_value}'

        # --- Apply daily bonus after successful record ---
        if check_bonus:
            User.add_daily_bonus(user_id)
            message += '\n🎁 Daily bonus: +10 XP'

        t_done = perf_counter()
        logger.info(
            f'/record timings: total={t_done - t0:.3f}s, '
            f'before_insert={t_before_insert - t0:.3f}s, '
            f'insert_block={t_after_insert - t_before_insert:.3f}s, '
            f'daily_bonus={t_done - t_after_insert:.3f}s'
        )

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
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityRecordsCog(bot))
