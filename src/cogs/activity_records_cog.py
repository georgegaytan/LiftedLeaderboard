from datetime import date

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from src.components.activity_records import RecentRecordsView
from src.services.db_manager import DBManager


class ActivityRecordsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete for category ---
    async def category_autocomplete(self, interaction: Interaction, current: str):
        '''Autocomplete available categories from the DB.'''
        with DBManager() as db:
            categories = db.fetchall(
                '''
                SELECT DISTINCT category
                FROM activities
                WHERE category LIKE ? AND is_archived = 0
                ORDER BY category ASC
                LIMIT 25
                ''',
                (f'%{current}%',),
            )
            return [
                app_commands.Choice(name=row['category'], value=row['category'])
                for row in categories
            ]

    # --- Autocomplete for activity based on selected category ---
    async def activity_autocomplete(self, interaction: Interaction, current: str):
        '''Autocomplete activity names within the selected category.'''
        # Check what category the user has currently selected
        category = interaction.namespace.category
        if not category:
            return []  # No category selected yet

        with DBManager() as db:
            activities = db.fetchall(
                '''
                SELECT name
                FROM activities
                WHERE category = ? AND name LIKE ? AND is_archived = 0
                ORDER BY name ASC
                LIMIT 25
                ''',
                (category, f'%{current}%'),
            )
            return [
                app_commands.Choice(name=row['name'], value=row['name'])
                for row in activities
            ]

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

        try:
            date_obj = date.fromisoformat(date_value)
        except ValueError:
            await interaction.response.send_message(
                '❌ Invalid date format. Use YYYY-MM-DD.', ephemeral=True
            )
            return

        # Optionally convert back to string to normalize
        date_value = date_obj.isoformat()

        with DBManager() as db:
            # --- Ensure user exists ---
            db.execute(
                '''
                INSERT INTO users (id, display_name)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name
                ''',
                (user_id, display_name),
            )

            # --- Daily bonus check (first record today) ---
            check_bonus = False
            today_str = date.today().isoformat()
            if date_value == today_str:
                already_row = db.fetchone(
                    'SELECT 1 FROM activity_records '
                    'WHERE user_id = ? AND date_occurred = ? LIMIT 1',
                    (user_id, today_str),
                )
                check_bonus = already_row is None

            # --- Lookup activity ---
            activity_row = db.fetchone(
                'SELECT id, xp_value FROM activities WHERE name = ? AND category = ?',
                (activity, category),
            )

            if not activity_row:
                await interaction.response.send_message(
                    f'❌ Activity "{activity}" not found in category "{category}".',
                    ephemeral=True,
                )
                return

            activity_id = activity_row['id']

            # --- Record the activity ---
            db.execute(
                '''
                INSERT INTO activity_records (user_id, activity_id, note, date_occurred)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, activity_id, note, date_value),
            )

            # XP is handled automatically by trigger
            message = f"✅ Recorded: **{activity}** (+{activity_row['xp_value']} XP)"
            message += f'\n📂 Category: {category}'
            if note:
                message += f'\n📝 _{note}_'
            if date_occurred:
                message += f'\n📅 Date: {date_value}'

            # --- Apply daily bonus after successful record ---
            if check_bonus:
                db.execute(
                    'UPDATE users '
                    'SET total_xp = total_xp + 10, updated_at = CURRENT_TIMESTAMP '
                    'WHERE id = ?',
                    (user_id,),
                )
                message += '\n🎁 Daily bonus: +10 XP'

            await interaction.response.send_message(message)

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

        if sort_mode == 'created':
            order_clause = 'ORDER BY ar.created_at DESC, ar.id DESC'
        elif sort_mode == 'updated':
            order_clause = 'ORDER BY ar.updated_at DESC, ar.id DESC'
        else:  # Default: occurred
            order_clause = 'ORDER BY ar.date_occurred DESC, ar.id DESC'

        with DBManager() as db:
            rows = db.fetchall(
                f'''
                SELECT ar.id AS id,
                       ar.note AS note,
                       ar.date_occurred AS date_occurred,
                       ar.created_at AS created_at,
                       ar.updated_at AS updated_at,
                       a.name AS activity_name,
                       a.category AS category,
                       a.xp_value AS xp_value
                FROM activity_records ar
                JOIN activities a ON a.id = ar.activity_id
                WHERE ar.user_id = ?
                {order_clause}
                LIMIT ?
                ''',
                (user_id, lim),
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
