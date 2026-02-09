import logging
from datetime import date, datetime, timezone

import discord
import pendulum
from discord import Interaction

from src.models.activity import Activity
from src.models.activity_record import ActivityRecord
from src.models.user import User

logger = logging.getLogger(__name__)


class RecentRecordsView(discord.ui.View):
    def __init__(self, requestor_id: int, records: list[dict]):
        super().__init__(timeout=120)
        self.requestor_id = requestor_id
        self.records = records

        options = []
        for idx, r in enumerate(records, start=1):
            label = f"{idx}. {r['activity_name']}"
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
    def __init__(
        self, record: dict, requestor_id: int, interaction: Interaction | None = None
    ):
        super().__init__(timeout=180)
        self.record = record
        self.requestor_id = requestor_id
        self.interaction = interaction
        self.selected_category: str = record['category']
        self.selected_activity: str = record['activity_name']
        self.current_note: str | None = record['note']
        d = record['date_occurred']
        self.current_date: str = d.isoformat() if isinstance(d, date) else str(d)
        self.message_id = record.get('message_id')  # Store message_id from the record

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

        record_id = int(self.values[0])
        record = next((r for r in view.records if r['id'] == record_id), None)
        if not record:
            await interaction.response.send_message('Record not found.', ephemeral=True)
            return

        edit_view = RecordEditView(
            record=record, requestor_id=view.requestor_id, interaction=interaction
        )
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
        original_message_id: int | None = None,
        original_channel_id: int | None = None,
    ):
        super().__init__(title='Edit Note/Date')
        self.record_id = record_id
        self.staged_activity_id = staged_activity_id
        self.staged_category = staged_category
        self.staged_activity_name = staged_activity_name
        self.parent_view = parent_view
        self.original_message_id = original_message_id
        self.original_channel_id = original_channel_id

        self.note = discord.ui.TextInput(
            label='Note about Activity (Optional)',
            style=discord.TextStyle.paragraph,
            required=False,
            default=current_note or '',
            max_length=500,
        )
        self.date_occurred = discord.ui.TextInput(
            label='Date Activity Occurred (YYYY-MM-DD format)',
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
            # Parse the date using pendulum for flexible input
            parsed_date = pendulum.parse(date_val, strict=False)
            if not parsed_date:
                raise ValueError('Could not parse date')
            # Convert to date object and back to ISO format for consistency
            date_val = parsed_date.date().isoformat()
        except Exception:
            await interaction.response.send_message(
                '❌ Invalid date format. '
                'Try formats like: YYYY-MM-DD, MM/DD/YYYY, or "yesterday"',
                ephemeral=True,
            )
            return

        # Get the current record to ensure we have the latest data
        record = ActivityRecord.get(self.record_id)
        if not record:
            await interaction.response.send_message(
                '❌ Record not found.',
                ephemeral=True,
            )
            return

        # Get the activity details to ensure we have the correct XP value
        activity = Activity.get(self.staged_activity_id)
        if not activity:
            await interaction.response.send_message(
                '❌ Activity not found.',
                ephemeral=True,
            )
            return

        # Update the record in the database
        group_key = ActivityRecord._activity_group_key(
            self.staged_category, self.staged_activity_name
        )
        if group_key == 'steps_daily':
            dup = ActivityRecord.has_group_activity_on_date(
                user_id=record['user_id'],
                group_key=group_key,
                date_iso=date_val,
                exclude_record_id=self.record_id,
            )
            if dup:
                await interaction.response.send_message(
                    '❌ You already recorded a Daily Steps activity for that day.',
                    ephemeral=True,
                )
                return
        else:
            dup = ActivityRecord.has_activity_on_date(
                user_id=record['user_id'],
                activity_id=self.staged_activity_id,
                date_iso=date_val,
                exclude_record_id=self.record_id,
            )
            if dup:
                await interaction.response.send_message(
                    '❌ You already recorded that activity for that day.',
                    ephemeral=True,
                )
                return

        if group_key in {
            'steps_weekly',
            'recovery_weekly_sleep',
            'diet_weekly_no_alcohol',
        }:
            weekly_dup = ActivityRecord.has_group_activity_in_week(
                user_id=record['user_id'],
                group_key=group_key,
                date_iso=date_val,
                exclude_record_id=self.record_id,
            )
            if weekly_dup:
                await interaction.response.send_message(
                    '❌ You already recorded a weekly version of that '
                    'activity in the last 7 days.',
                    ephemeral=True,
                )
                return

        ActivityRecord.update_record(
            record_id=self.record_id,
            activity_id=self.staged_activity_id,
            note=(note_val if note_val != '' else None),
            date_occurred=date_val,
        )

        # Build the updated message content with the correct XP value
        xp_value = activity.get('xp_value', 0)
        message_content = (
            f'✅ Recorded: **{self.staged_activity_name}** (+{xp_value} XP)\n'
        )
        if note_val:
            message_content += f'📝 _{note_val}_\n'
        message_content += f'📂 Category: {self.staged_category}\n'
        today_iso = datetime.now(timezone.utc).date().isoformat()
        if date_val != today_iso:
            message_content += f'📅 Date: {date_val}'

        # Defer the response first to prevent interaction timeout
        await interaction.response.defer(ephemeral=True)

        try:
            # Try to edit the original message
            if self.original_channel_id and self.original_message_id:
                channel = interaction.guild.get_channel(self.original_channel_id)
                if channel and isinstance(
                    channel, (discord.TextChannel, discord.Thread)
                ):
                    try:
                        message = await channel.fetch_message(
                            int(self.original_message_id)
                        )
                        await message.edit(content=message_content)
                        await interaction.followup.send(
                            f'✅ Updated record: {self.staged_activity_name} '
                            f'({self.staged_category})',
                            ephemeral=True,
                            delete_after=5,
                        )
                        return
                    except discord.NotFound:
                        logger.warning(
                            f'Original message {self.original_message_id} '
                            f'not found in channel {self.original_channel_id}'
                        )
                    except discord.Forbidden:
                        logger.warning(
                            f'Missing permissions to edit message '
                            f'{self.original_message_id} '
                            f'in channel {self.original_channel_id}'
                        )
                    except Exception as e:
                        logger.error(f'Error editing message: {e}')

                        # Fallback to send a new message if we can't edit the original
                        await interaction.followup.send(
                            f'✅ Updated record: {self.staged_activity_name} '
                            f'({self.staged_category})',
                            ephemeral=True,
                        )

        except Exception as e:
            logger.error(f'Error in RecordEditModal.on_submit: {e}')
            try:
                await interaction.followup.send(
                    f'✅ Updated record but failed to update message: {str(e)}',
                    ephemeral=True,
                )
            except Exception as e2:
                logger.error(f'Failed to send error message to user: {e2}')


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

        # Fetch record to inspect created_at and user_id
        rec = ActivityRecord.get(self.record_id)
        if not rec:
            await interaction.response.send_message(
                '❌ Record not found or already deleted.', ephemeral=True
            )
            return

        user_id = rec.get('user_id')
        created_at: datetime = rec.get('created_at')  # type: ignore[assignment]
        message_id = rec.get('message_id')

        # If this record is the only one created today for the user, remove daily bonus
        try:
            today_iso = datetime.now(timezone.utc).date().isoformat()
            if hasattr(created_at, 'date'):
                created_date_iso = created_at.date().isoformat()
            else:
                created_date_iso = str(created_at)[:10]

            if created_date_iso == today_iso and user_id is not None:
                cnt = ActivityRecord.count_on_created_date(user_id, today_iso)
                if cnt == 1:
                    User.remove_daily_bonus(user_id)
        except Exception:
            # Best-effort; proceed with deletion regardless
            pass

        # Best-effort: delete the associated Discord message if we know its ID
        if message_id:
            try:
                channel = interaction.channel
                # TextChannel, Thread, DMChannel all implement fetch_message
                if channel and hasattr(channel, 'fetch_message'):
                    try:
                        msg = await channel.fetch_message(int(message_id))
                        await msg.delete()
                    except discord.NotFound:
                        logger.warning(
                            f'Associated message {message_id} not found in channel '
                            f'{getattr(channel, "id", "unknown")}'
                        )
                    except discord.Forbidden:
                        logger.warning(
                            f'Missing permissions to delete message {message_id} '
                            f'in channel {getattr(channel, "id", "unknown")}'
                        )
                    except Exception as e:
                        logger.error(
                            f'Error deleting associated message {message_id}: {e}'
                        )
            except Exception as e:
                logger.error(
                    f'Unexpected error while deleting associated message '
                    f'{message_id}: {e}'
                )

        ActivityRecord.delete_record(self.record_id)

        await interaction.response.send_message(
            '✅ Record deleted successfully!', ephemeral=True
        )


class DeleteButton(discord.ui.Button):
    def __init__(self, parent_view: RecordEditView):
        super().__init__(label='Delete', style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        view = self.parent_view
        if not isinstance(view, RecordEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return

        modal = DeleteConfirmModal(record_id=view.record['id'])
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

        # Get the activity ID for the selected activity
        activity_name = v.selected_activity
        category = v.selected_category
        row = Activity.get_by_name_category(activity_name, category, active_only=True)
        if not row:
            await interaction.response.send_message(
                '❌ Error: Activity not found.', ephemeral=True
            )
            return

        # Show the edit modal
        modal = RecordEditModal(
            record_id=v.record['id'],
            staged_activity_id=row['id'],
            staged_category=category,
            staged_activity_name=activity_name,
            current_note=v.current_note,
            current_date=v.current_date,
            parent_view=v,
            original_message_id=v.message_id,  # Use the stored message_id
            original_channel_id=(
                getattr(interaction.channel, 'id', None)
                if interaction.channel
                else None
            ),
        )
        await interaction.response.send_modal(modal)
