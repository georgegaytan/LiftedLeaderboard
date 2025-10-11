from discord.ext import commands
from discord import app_commands, Interaction
from datetime import date
from src.services.db_manager import fetchall, fetchone, execute

# TODO POC: Test functionalities after DB is populated
class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete for category ---
    async def category_autocomplete(self, interaction: Interaction, current: str):
        """Autocomplete available categories from the DB."""
        categories = fetchall(
            """
            SELECT DISTINCT category
            FROM activities
            WHERE category LIKE ?
            ORDER BY category ASC
            LIMIT 25
            """,
            (f"%{current}%",),
        )
        return [
            app_commands.Choice(name=row["category"], value=row["category"])
            for row in categories
        ]

    # --- Autocomplete for activity based on selected category ---
    async def activity_autocomplete(self, interaction: Interaction, current: str):
        """Autocomplete activity names within the selected category."""
        # Check what category the user has currently selected
        category = interaction.namespace.category
        if not category:
            return []  # No category selected yet

        activities = fetchall(
            """
            SELECT name
            FROM activities
            WHERE category = ? AND name LIKE ?
            ORDER BY name ASC
            LIMIT 25
            """,
            (category, f"%{current}%"),
        )
        return [
            app_commands.Choice(name=row["name"], value=row["name"])
            for row in activities
        ]

    # --- Command: /record ---
    @app_commands.command(name="record", description="Record an activity to earn XP")
    @app_commands.describe(
        category="Choose the category of activity (e.g., Running, Swimming, etc.)",
        activity="Select the specific activity",
        note="Optional note about your session",
        date_occurred="When the activity occurred (default: today)"
    )
    @app_commands.autocomplete(category=category_autocomplete, activity=activity_autocomplete)
    async def record(
        self,
        interaction: Interaction,
        category: str,
        activity: str,
        note: str | None = None,
        date_occurred: str | None = None,
    ):
        """Record an activity and automatically award XP."""
        user_id = interaction.user.id
        display_name = interaction.user.display_name
        date_value = date_occurred or date.today().isoformat()

        # --- Ensure user exists ---
        execute(
            """
            INSERT INTO users (user_id, display_name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET display_name=excluded.display_name
            """,
            (user_id, display_name),
        )

        # --- Lookup activity ---
        activity_row = fetchone(
            "SELECT id, xp_value FROM activities WHERE name = ? AND category = ?",
            (activity, category),
        )

        if not activity_row:
            await interaction.response.send_message(
                f"❌ Activity '{activity}' not found in category '{category}'.",
                ephemeral=True,
            )
            return

        activity_id = activity_row["id"]

        # --- Record the activity ---
        execute(
            """
            INSERT INTO activity_records (user_id, activity_id, note, date_occurred)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, activity_id, note, date_value),
        )

        # XP is handled automatically by trigger
        message = f"✅ Recorded: **{activity}** (+{activity_row['xp_value']} XP)"
        message += f"\n📂 Category: {category}"
        if note:
            message += f"\n📝 _{note}_"
        if date_occurred:
            message += f"\n📅 Date: {date_value}"

        await interaction.response.send_message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityCog(bot))
