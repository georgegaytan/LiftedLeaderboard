import discord
from discord import Interaction

from src.services.db_manager import DBManager


class BaseConfirmView(discord.ui.View):
    '''Base confirmation view with confirm/cancel buttons.'''

    def __init__(
        self,
        *,
        timeout: int = 30,
        confirm_label: str = '✅ Confirm',
        cancel_label: str = '❌ Cancel',
    ):
        super().__init__(timeout=timeout)
        self.value: bool | None = None
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, 'message'):
            await self.message.edit(content='⏰ Confirmation timed out.', view=self)

    @discord.ui.button(label='✅ Confirm', style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(content='✅ Confirmed.', view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='❌ Canceled.', view=None)
        self.value = False
        self.stop()


class ResetConfirmView(BaseConfirmView):
    '''Specialized confirmation for leaderboard resets'''

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label='⚠️ Confirm Reset', style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content='Reset confirmed. Clearing all XP...', view=None
        )
        self.value = True
        self.stop()


# TODO: DRY this up with the activity_records CategorySelect
class CategorySelect(discord.ui.Select):
    '''Dropdown to select an existing category from the DB.'''

    def __init__(self, categories: list[str]):
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(
            placeholder='Select a category...',
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction):
        '''When a category is chosen, open the modal to add the activity.'''
        selected_category = self.values[0]
        await interaction.response.send_modal(AddActivityModal(selected_category))


class AddActivityModal(discord.ui.Modal):
    '''Modal to input activity name and XP value.'''

    activity_name = discord.ui.TextInput(
        label='Activity Name',
        placeholder='i.e. Hiking for N hours, Meditation, etc.',
        required=True,
        max_length=100,
    )

    xp_value = discord.ui.TextInput(
        label='XP Value',
        placeholder='Enter a positive integer (i.e. 50)',
        required=True,
        style=discord.TextStyle.short,
    )

    def __init__(self, category: str):
        super().__init__(title='Add New Activity')
        self.category = category

    async def on_submit(self, interaction: Interaction):
        '''Insert the new activity into the DB.'''
        name = str(self.activity_name.value).strip()
        xp_str = str(self.xp_value.value).strip()

        try:
            xp_value = int(xp_str)
            assert xp_value > 0
        except ValueError:
            await interaction.response.send_message(
                f'❌ Invalid XP value: `{xp_str}`. Please enter a positive integer.',
                ephemeral=True,
            )
            return

        with DBManager() as db:
            db.execute(
                '''
                INSERT INTO activities (name, category, xp_value)
                VALUES (?, ?, ?)
                ON CONFLICT (name)
                DO UPDATE SET xp_value = excluded.xp_value
                ''',
                (name, self.category, xp_value),
            )

        await interaction.response.send_message(
            f'✅ Activity **{name}** (Category: **{self.category}**) '
            f'added with **{xp_value} XP**!',
            ephemeral=True,
        )


class CategorySelectView(discord.ui.View):
    '''View that displays the category dropdown.'''

    def __init__(self, categories: list[str]):
        super().__init__(timeout=60)
        self.add_item(CategorySelect(categories))
