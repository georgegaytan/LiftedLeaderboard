import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from src.models.activity import Activity
from src.models.activity_record import ActivityRecord
from src.models.quest import Quest
from src.models.quest_roll import QuestRoll

logger = logging.getLogger(__name__)


class QuestOption(TypedDict):
    activity_id: int
    name: str
    category: str
    xp_value: int
    is_new: bool


class QuestSelectionView(discord.ui.View):
    def __init__(self, user_id: int, options: list[QuestOption]):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.options = options
        self.selected_option: QuestOption | None = None

        # Create Select Menu
        select = discord.ui.Select(
            placeholder='Choose your quest...',
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=f'{opt["name"]} ({opt["category"]})',
                    description=f'Reward: {50 + (100 if opt["is_new"] else 0)} XP'
                    + (' (New!)' if opt['is_new'] else ''),
                    value=str(opt['activity_id']),
                )
                for opt in options
            ],
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This isn't your quest roll!", ephemeral=True
            )
            return

        selected_id = int(interaction.data['values'][0])  # type: ignore
        self.selected_option = next(
            (o for o in self.options if o['activity_id'] == selected_id), None
        )

        if self.selected_option:
            # Check if user has already accepted a quest from this roll (double check)
            # This is to prevent race conditions or if they somehow reused the view
            # But QuestRoll.mark_accepted is called after, so we should check before.
            # However, the view is ephemeral, so it's unlikely they can reuse it easily
            # after the roll changes, but let's be safe?
            # Actually, we'll rely on the command check mainly, but let's just mark it.
            await interaction.response.defer()
            self.stop()


class QuestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='quest',
        description='Roll 5 random activities and choose one as a quest for bonus XP',
    )
    async def quest(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        # Check for existing active quest
        active_quest = await asyncio.to_thread(Quest.get_active, user_id)
        if active_quest:
            now = datetime.now(timezone.utc)
            deadline = active_quest['deadline']
            if deadline > now:
                await interaction.followup.send(
                    f'⚠️ You already have an active quest: '
                    f'**{active_quest["activity_name"]}**\n'
                    f"Deadline: {discord.utils.format_dt(deadline, 'R')}",
                    ephemeral=True,
                )
                return
            else:
                # Clean up expired quest silently
                await asyncio.to_thread(Quest.delete_quest, active_quest['id'])

        # Get sticky roll
        def get_new_activity_ids():
            activities = Activity.get_random(5)
            return [a['id'] for a in activities]

        quest_roll = await asyncio.to_thread(
            QuestRoll.get_or_create, user_id, get_new_activity_ids
        )

        # Check if already accepted a quest from this roll
        if quest_roll['has_accepted']:
            # Calculate when the next roll is available
            date_rolled = quest_roll['date_rolled']
            if isinstance(date_rolled, str):
                date_rolled = datetime.fromisoformat(date_rolled)
            if date_rolled.tzinfo is None:
                date_rolled = date_rolled.replace(tzinfo=timezone.utc)

            next_roll = date_rolled + timedelta(days=7)

            await interaction.followup.send(
                f'⏳ You have already accepted a quest this week.\n'
                f"Next roll available: {discord.utils.format_dt(next_roll, 'R')}",
                ephemeral=True,
            )
            return

        # Fetch activities for the roll
        activity_ids = quest_roll['activity_ids']
        # Ensure it is a list (JSONB might return whatever)
        if isinstance(activity_ids, str):
            # Should not happen with psycopg/jsonb usually but depends on adapter
            import json

            activity_ids = json.loads(activity_ids)

        activities = await asyncio.to_thread(Activity.get_by_ids, activity_ids)

        if not activities:
            await interaction.followup.send(
                '❌ No activities available for quests.', ephemeral=True
            )
            return

        # Check existing records to determine if "new"
        quest_options: list[QuestOption] = []

        for act in activities:
            has_done = await asyncio.to_thread(
                ActivityRecord.has_any_record, user_id, act['id']
            )
            quest_options.append(
                {
                    'activity_id': act['id'],
                    'name': act['name'],
                    'category': act['category'],
                    'xp_value': act['xp_value'],
                    'is_new': not has_done,
                }
            )

        view = QuestSelectionView(user_id, quest_options)
        await interaction.followup.send(
            '🎲 **Quest Roll**\n'
            'Choose one of the following activities to complete within 7 days!',
            view=view,
            ephemeral=True,
        )

        timed_out = await view.wait()
        if timed_out:
            await interaction.followup.send(
                'Quest selection timed out.', ephemeral=True
            )
            return

        if view.selected_option:
            opt = view.selected_option
            deadline = datetime.now(timezone.utc) + timedelta(days=7)

            # Mark roll as accepted
            await asyncio.to_thread(QuestRoll.mark_accepted, user_id)

            await asyncio.to_thread(
                Quest.create_new,
                user_id=user_id,
                activity_id=opt['activity_id'],
                deadline=deadline,
                is_new_bonus=opt['is_new'],
            )

            bonus_text = ' +100 New Activity Bonus!' if opt['is_new'] else '!'
            # Announce in channel (publicly)
            try:
                if interaction.channel:
                    await interaction.channel.send(
                        f'⚔️ **{interaction.user.display_name}** '
                        'accepted a new quest!\n'
                        f'Activity: **{opt["name"]}**\n'
                        f'Deadline: {discord.utils.format_dt(deadline, "R")}\n'
                        f'Potential Reward: {opt["xp_value"]} XP + 50 Quest XP'
                        f'{bonus_text}',
                    )
            except discord.Forbidden:
                await interaction.followup.send(
                    'ERROR: Missing permissions '
                    'to announce quest in channel.\n'
                    f'✅ **Quest Accepted!**\n'
                    f'Activity: **{opt["name"]}**\n'
                    f'Deadline: {discord.utils.format_dt(deadline, "R")}\n'
                    f'Potential Reward: {opt["xp_value"]} XP + 50 Quest XP'
                    f'{bonus_text}',
                    ephemeral=True,
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestCog(bot))
