from datetime import date

import discord
from discord import Interaction

from src.models.activity import Activity
from src.models.activity_record import ActivityRecord


class RecentRecordsView(discord.ui.View):
    def __init__(self, requestor_id: int, records: list[dict]):
        super().__init__(timeout=120)
        self.requestor_id = requestor_id
        self.records = records

        options = []
        for idx, r in enumerate(records, start=1):
            label = f"{idx}. {r['activity_name']}"
            # Coerce date to ISO string for Discord component JSON
            d = r['date_occurred']
            d_str = d.isoformat() if isinstance(d, date) else str(d)
            description = f"{r['category']} • {d_str}"
            options.append(
                discord.SelectOption(
                    label=label, description=description, value=str(r['id'])
                )
            )

        self.add_item(_RecordSelect(options))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.requestor_id:
            await interaction.response.send_message(
                'You cannot interact with this view.', ephemeral=True
            )
            return False
        return True


class RecordEditView(discord.ui.View):
    def __init__(self, record: dict, requestor_id: int):
        super().__init__(timeout=180)
        self.record = record
        self.requestor_id = requestor_id
        self.selected_category: str = record['category']
        self.selected_activity: str = record['activity_name']
        self.current_note: str | None = record['note']
        # Ensure current_date is a string (Postgres DATE may come as date object)
        d = record['date_occurred']
        self.current_date: str = d.isoformat() if isinstance(d, date) else str(d)

        categories = self._fetch_categories()
        activities = self._fetch_activities(self.selected_category)

        self.category_select = CategorySelect(categories, self.selected_category)
        self.activity_select = ActivitySelect(activities, self.selected_activity)

        self.add_item(self.category_select)
        self.add_item(self.activity_select)
        self.add_item(DeleteButton(self))
        self.add_item(ContinueButton(self))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.requestor_id:
            await interaction.response.send_message(
                'You cannot interact with this view.', ephemeral=True
            )
            return False
        return True

    def _fetch_categories(self) -> list[str]:
        return Activity.list_categories(active_only=True, limit=25)

    def _fetch_activities(self, category: str) -> list[str]:
        if not category:
            return []
        rows = Activity.list_by_category(category, active_only=True, limit=25)
        return [r['name'] for r in rows]


class _RecordSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(
            placeholder='Select a record to edit…',
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction):
        view = self.view
        if not isinstance(view, RecentRecordsView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return

        if not self.values:
            await interaction.response.send_message(
                'No record selected.', ephemeral=True
            )
            return

        record_id = int(self.values[0])
        rec = next((r for r in view.records if r['id'] == record_id), None)
        if not rec:
            await interaction.response.send_message('Record not found.', ephemeral=True)
            return

        edit_view = RecordEditView(record=rec, requestor_id=view.requestor_id)
        await interaction.response.edit_message(view=edit_view)


class CategorySelect(discord.ui.Select):
    def __init__(self, categories: list[str], current: str):
        options = [
            discord.SelectOption(label=c, value=c, default=(c == current))
            for c in categories
        ]
        super().__init__(
            placeholder='Select category…', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: Interaction):
        v = self.view
        if not isinstance(v, RecordEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return
        v.selected_category = self.values[0]
        v.category_select.options = [
            discord.SelectOption(
                label=c.label, value=c.value, default=(c.value == v.selected_category)
            )
            for c in self.options
        ]
        activities = v._fetch_activities(v.selected_category)
        v.selected_activity = activities[0] if activities else ''
        v.activity_select.options = [
            discord.SelectOption(label=a, value=a, default=(a == v.selected_activity))
            for a in activities
        ]
        await interaction.response.edit_message(view=v)


class ActivitySelect(discord.ui.Select):
    def __init__(self, activities: list[str], current: str):
        options = [
            discord.SelectOption(label=a, value=a, default=(a == current))
            for a in activities
        ]
        super().__init__(
            placeholder='Select activity…', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: Interaction):
        v = self.view
        if not isinstance(v, RecordEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return
        v.selected_activity = self.values[0]
        await interaction.response.defer()


class RecordEditModal(discord.ui.Modal):
    def __init__(
        self,
        record_id: int,
        staged_activity_id: int,
        staged_category: str,
        staged_activity_name: str,
        current_note: str | None,
        current_date: str,
        parent_view: RecordEditView | None = None,
    ):
        super().__init__(title='Edit Note/Date')
        self.record_id = record_id
        self.staged_activity_id = staged_activity_id
        self.staged_category = staged_category
        self.staged_activity_name = staged_activity_name
        self.parent_view = parent_view

        self.note = discord.ui.TextInput(
            label='Note about Activity (Optional)',
            style=discord.TextStyle.paragraph,
            required=False,
            default=current_note or '',
            max_length=500,
        )
        self.date_occurred = discord.ui.TextInput(
            label='Date Activity Occurred (YYYY-MM-DD)',
            style=discord.TextStyle.short,
            required=True,
            default=current_date,
            max_length=10,
        )

        self.add_item(self.note)
        self.add_item(self.date_occurred)

    async def on_submit(self, interaction: Interaction):
        note_val = str(self.note.value).strip() if self.note.value else None
        date_val = str(self.date_occurred.value).strip()

        try:
            _ = date.fromisoformat(date_val)
        except Exception:
            await interaction.response.send_message(
                '❌ Invalid date format. Use YYYY-MM-DD.', ephemeral=True
            )
            return

        ActivityRecord.update_record(
            record_id=self.record_id,
            activity_id=self.staged_activity_id,
            note=(note_val if note_val != '' else None),
            date_occurred=date_val,
        )

        await interaction.response.send_message(
            f'✅ Updated record: {self.staged_activity_name} ({self.staged_category}) '
            f'on {date_val}',
            ephemeral=True,
        )


class DeleteConfirmModal(discord.ui.Modal):
    def __init__(self, record_id: int):
        super().__init__(title='Confirm Delete')
        self.record_id = record_id

        self.confirm_input = discord.ui.TextInput(
            label='Type DELETE to confirm',
            style=discord.TextStyle.short,
            required=True,
            max_length=6,
        )
        self.add_item(self.confirm_input)

    async def on_submit(self, interaction: Interaction):
        if self.confirm_input.value.strip().upper() != 'DELETE':
            await interaction.response.send_message(
                '❌ Confirmation failed. Record not deleted.', ephemeral=True
            )
            return

        ActivityRecord.delete_record(self.record_id)

        await interaction.response.send_message(
            '✅ Record deleted successfully!', ephemeral=True
        )


class DeleteButton(discord.ui.Button):
    def __init__(self, parent_view: RecordEditView):
        super().__init__(label='Delete', style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        v = self.parent_view
        if not isinstance(v, RecordEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return

        modal = DeleteConfirmModal(record_id=v.record['id'])
        await interaction.response.send_modal(modal)


class ContinueButton(discord.ui.Button):
    def __init__(self, parent_view: RecordEditView):
        super().__init__(label='Continue', style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        v = self.parent_view
        if not isinstance(v, RecordEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return

        category = v.selected_category
        activity_name = v.selected_activity

        if not category or not activity_name:
            await interaction.response.send_message(
                'Please select a category and activity first.', ephemeral=True
            )
            return

        row = Activity.get_by_name_category(activity_name, category, active_only=True)

        if not row:
            await interaction.response.send_message(
                '❌ Selected activity not found.', ephemeral=True
            )
            return

        modal = RecordEditModal(
            record_id=v.record['id'],
            staged_activity_id=row['id'],
            staged_category=category,
            staged_activity_name=activity_name,
            current_note=v.current_note,
            current_date=v.current_date,
            parent_view=v,
        )
        await interaction.response.send_modal(modal)
