import discord


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
