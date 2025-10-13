from __future__ import annotations

from datetime import date

import discord
from discord import Interaction

from src.services.db_manager import DBManager


class RecordEditModal(discord.ui.Modal):
    def __init__(
        self,
        record_id: int,
        current_note: str | None,
        current_date: str,
        parent_view: RecordEditView | None = None,
    ):
        super().__init__(title='Edit Note/Date')
        self.record_id = record_id
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
        note_val = str(self.note.value).strip() if self.note.value is not None else None
        date_val = str(self.date_occurred.value).strip()

        try:
            _ = date.fromisoformat(date_val)
        except Exception:
            await interaction.response.send_message(
                '❌ Invalid date format. Use YYYY-MM-DD.', ephemeral=True
            )
            return

        # Update in DB immediately
        with DBManager() as db:
            db.execute(
                'UPDATE activity_records SET note = ?, date_occurred = ? WHERE id = ?',
                (note_val if note_val != '' else None, date_val, self.record_id),
            )

        await interaction.response.send_message(
            '✅ Record updated successfully!', ephemeral=True
        )


class DeleteConfirmModal(discord.ui.Modal):
    def __init__(self, record_id: int):
        super().__init__(title='Confirm Delete')
        self.record_id = record_id

        # A single text input just to confirm
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

        # Delete the record
        with DBManager() as db:
            db.execute('DELETE FROM activity_records WHERE id = ?', (self.record_id,))

        await interaction.response.send_message(
            '✅ Record deleted successfully!', ephemeral=True
        )


class RecentRecordsView(discord.ui.View):
    def __init__(self, requestor_id: int, records: list[dict]):
        super().__init__(timeout=120)
        self.requestor_id = requestor_id
        self.records = records

        options = []
        for idx, r in enumerate(records, start=1):
            label = f"{idx}. {r['activity_name']}"
            description = f"{r['category']} • {r['date_occurred']}"
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


class RecordEditView(discord.ui.View):
    def __init__(self, record: dict, requestor_id: int):
        super().__init__(timeout=180)
        self.record = record
        self.requestor_id = requestor_id
        self.selected_category: str = record['category']
        self.selected_activity: str = record['activity_name']
        self.current_note: str | None = record['note']
        self.current_date: str = record['date_occurred']

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
        with DBManager() as db:
            rows = db.fetchall(
                'SELECT DISTINCT category '
                'FROM activities '
                'WHERE is_archived = 0 '
                'ORDER BY category ASC '
                'LIMIT 25'
            )
        return [r['category'] for r in rows]

    def _fetch_activities(self, category: str) -> list[str]:
        if not category:
            return []
        with DBManager() as db:
            rows = db.fetchall(
                'SELECT name '
                'FROM activities '
                'WHERE category = ? AND is_archived = 0 '
                'ORDER BY name ASC '
                'LIMIT 25',
                (category,),
            )
        return [r['name'] for r in rows]


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
        # Update category select defaults
        v.category_select.options = [
            discord.SelectOption(
                label=c.label, value=c.value, default=(c.value == v.selected_category)
            )
            for c in self.options
        ]
        # Refresh activities
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

        # Show confirmation modal
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

        # Persist category/activity changes first
        with DBManager() as db:
            row = db.fetchone(
                'SELECT id '
                'FROM activities '
                'WHERE category = ? AND name = ? AND is_archived = 0',
                (category, activity_name),
            )
            if not row:
                await interaction.response.send_message(
                    'Selected activity not found.', ephemeral=True
                )
                return
            activity_id = row['id']
            db.execute(
                'UPDATE activity_records SET activity_id = ? WHERE id = ?',
                (activity_id, v.record['id']),
            )

        # Now pop up the modal for note/date edit
        modal = RecordEditModal(
            record_id=v.record['id'],
            current_note=v.current_note,
            current_date=v.current_date,
            parent_view=v,
        )
        await interaction.response.send_modal(modal)
