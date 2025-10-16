import discord
from discord import Interaction

from src.models.activity import Activity


class CategorySelectView(discord.ui.View):
    def __init__(self, categories: list[str]):
        super().__init__(timeout=60)
        self.add_item(CategorySelect(categories))


class ActivityEditView(discord.ui.View):
    def __init__(self, requestor_id: int):
        super().__init__(timeout=180)
        self.requestor_id = requestor_id
        self.selected_category: str = ''
        self.selected_activity: str = ''
        self.activity_id: int | None = None
        self.activity_is_archived: bool = False

        categories = self._fetch_categories()

        init_category = ''
        init_activities: list[dict] = []
        for c in categories:
            acts = self._fetch_activities(c)
            if acts:
                init_category = c
                init_activities = acts
                break

        self.selected_category = init_category
        if init_activities:
            self.activity_id = init_activities[0]['id']
            self.selected_activity = init_activities[0]['name']
            self.activity_is_archived = bool(init_activities[0]['is_archived'])

        self.category_select = ActivityCategorySelect(categories)
        self.category_select.options = [
            discord.SelectOption(
                label=c, value=c, default=(c == self.selected_category)
            )
            for c in categories
        ]

        self.activity_select = ActivityNameSelect(
            init_activities, current_id=self.activity_id
        )
        self.new_category_select = NewCategorySelect(categories)

        self.add_item(self.category_select)
        self.add_item(self.activity_select)
        self.add_item(self.new_category_select)
        self.archive_button = ArchiveButton(self)
        self.add_item(self.archive_button)
        self.add_item(ContinueEditButton(self))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.requestor_id:
            await interaction.response.send_message(
                'You cannot interact with this view.', ephemeral=True
            )
            return False
        return True

    def _fetch_categories(self) -> list[str]:
        return Activity.list_categories(active_only=False, limit=25)

    def _fetch_activities(self, category: str) -> list[dict]:
        if not category:
            return []
        rows: list[dict] = Activity.list_by_category(
            category, active_only=False, limit=25
        )
        return rows


class CategorySelect(discord.ui.Select):
    def __init__(self, categories: list[str]):
        options = [discord.SelectOption(label=cat) for cat in categories]
        super().__init__(
            placeholder='Select a category...',
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction):
        selected_category = self.values[0]
        await interaction.response.send_modal(AddActivityModal(selected_category))


class ActivityCategorySelect(discord.ui.Select):
    def __init__(self, categories: list[str]):
        options = [discord.SelectOption(label=c, value=c) for c in categories]
        super().__init__(
            placeholder='Select category…',
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: Interaction):
        view = self.view
        if not isinstance(view, ActivityEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return

        view.selected_category = self.values[0]
        activities = view._fetch_activities(view.selected_category)

        new_cat = ActivityCategorySelect([o.value for o in self.options])
        new_cat.options = [
            discord.SelectOption(
                label=o.label,
                value=o.value,
                default=(o.value == view.selected_category),
            )
            for o in self.options
        ]
        view.remove_item(view.category_select)
        view.category_select = new_cat
        view.add_item(new_cat)

        if activities:
            view.selected_activity = activities[0]['name']
            view.activity_id = activities[0]['id']
            view.activity_is_archived = bool(activities[0]['is_archived'])
            new_act = ActivityNameSelect(activities, current_id=view.activity_id)
            view.remove_item(view.activity_select)
            view.activity_select = new_act
            view.add_item(new_act)
        else:
            view.selected_activity = ''
            view.activity_id = None
            new_act = ActivityNameSelect([], current_id=None)
            view.remove_item(view.activity_select)
            view.activity_select = new_act
            view.add_item(new_act)

        if hasattr(view, 'archive_button') and isinstance(
            view.archive_button, ArchiveButton
        ):
            if view.activity_is_archived:
                view.archive_button.label = 'Unarchive'
                view.archive_button.style = discord.ButtonStyle.secondary
            else:
                view.archive_button.label = 'Archive'
                view.archive_button.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(view=view)


class ActivityNameSelect(discord.ui.Select):
    def __init__(self, activities: list[dict], current_id: int | None = None):
        options = [
            discord.SelectOption(
                label=(
                    f'[Archived] {a["name"]}' if bool(a['is_archived']) else a['name']
                ),
                value=str(a['id']),
                default=(a['id'] == current_id),
            )
            for a in activities
        ]
        super().__init__(
            placeholder='Select activity…',
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(self, interaction: Interaction):
        view = self.view
        if not isinstance(view, ActivityEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return
        if not self.values:
            await interaction.response.send_message(
                'No activity selected.', ephemeral=True
            )
            return
        view.activity_id = int(self.values[0])
        row = Activity.get(view.activity_id)
        view.selected_activity = row['name'] if row else ''
        view.activity_is_archived = bool(row['is_archived']) if row else False

        acts = view._fetch_activities(view.selected_category)
        new_act = ActivityNameSelect(acts, current_id=view.activity_id)
        view.remove_item(view.activity_select)
        view.activity_select = new_act
        view.add_item(new_act)

        if hasattr(view, 'archive_button') and isinstance(
            view.archive_button, ArchiveButton
        ):
            if view.activity_is_archived:
                view.archive_button.label = 'Unarchive'
                view.archive_button.style = discord.ButtonStyle.secondary
            else:
                view.archive_button.label = 'Archive'
                view.archive_button.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(view=view)


class NewCategorySelect(discord.ui.Select):
    def __init__(self, categories: list[str]):
        options = [discord.SelectOption(label=c, value=c) for c in categories]
        super().__init__(
            placeholder='Select new category (Optional)',
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class AddActivityModal(discord.ui.Modal):
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

        Activity.upsert_activity(name=name, category=self.category, xp_value=xp_value)

        await interaction.response.send_message(
            f'✅ Activity **{name}** (Category: **{self.category}**) '
            f'added with **{xp_value} XP**!',
            ephemeral=True,
        )


class ActivityEditModal(discord.ui.Modal):
    def __init__(
        self,
        activity_id: int,
        current_name: str,
        current_xp: int,
        staged_new_category: str | None,
    ):
        super().__init__(title='Edit Activity')
        self.activity_id = activity_id
        self.staged_new_category = staged_new_category

        self.activity_name = discord.ui.TextInput(
            label='Activity Name',
            placeholder='Enter new name…',
            required=True,
            max_length=100,
            default=current_name,
        )
        self.xp_value = discord.ui.TextInput(
            label='XP Value',
            placeholder='Enter a positive integer (i.e. 50)',
            required=True,
            style=discord.TextStyle.short,
            default=str(current_xp),
        )

        self.add_item(self.activity_name)
        self.add_item(self.xp_value)

    async def on_submit(self, interaction: Interaction):
        name = str(self.activity_name.value).strip()
        xp_str = str(self.xp_value.value).strip()

        try:
            xp_val = int(xp_str)
            assert xp_val > 0
        except Exception:
            await interaction.response.send_message(
                f'❌ Invalid XP value: `{xp_str}`. Please enter a positive integer.',
                ephemeral=True,
            )
            return

        try:
            row = Activity.get(self.activity_id)
            current_category = row['category'] if row else None
            final_category = (
                self.staged_new_category
                if self.staged_new_category
                else current_category
            )
            Activity.update(
                self.activity_id,
                {
                    'name': name,
                    'xp_value': xp_val,
                    'category': final_category,
                },
            )
        except Exception as e:
            await interaction.response.send_message(
                f'❌ Failed to update activity: {e}', ephemeral=True
            )
            return

        await interaction.response.send_message(
            f'✅ Activity updated to **{name}** with **{xp_val} XP**.',
            ephemeral=True,
        )


class ArchiveButton(discord.ui.Button):
    def __init__(self, parent_view: ActivityEditView):
        label = 'Unarchive' if parent_view.activity_is_archived else 'Archive'
        style = (
            discord.ButtonStyle.secondary
            if parent_view.activity_is_archived
            else discord.ButtonStyle.danger
        )
        super().__init__(label=label, style=style, row=3)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        v = self.parent_view
        if not isinstance(v, ActivityEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return
        if not v.activity_id:
            await interaction.response.send_message(
                'Select an activity first.', ephemeral=True
            )
            return

        new_flag = not v.activity_is_archived
        Activity.set_archived(v.activity_id, new_flag)

        v.activity_is_archived = new_flag
        self.label = 'Unarchive' if v.activity_is_archived else 'Archive'
        self.style = (
            discord.ButtonStyle.secondary
            if v.activity_is_archived
            else discord.ButtonStyle.danger
        )

        acts = v._fetch_activities(v.selected_category)
        v.activity_select.options = [
            discord.SelectOption(
                label=(f'[Archived] {a["name"]}' if a['is_archived'] else a['name']),
                value=str(a['id']),
                default=(a['id'] == v.activity_id),
            )
            for a in acts
        ]

        await interaction.response.edit_message(view=v)


class ContinueEditButton(discord.ui.Button):
    def __init__(self, parent_view: ActivityEditView):
        super().__init__(label='Continue', style=discord.ButtonStyle.secondary, row=3)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        v = self.parent_view
        if not isinstance(v, ActivityEditView):
            await interaction.response.send_message(
                'Internal error: invalid view.', ephemeral=True
            )
            return
        if not v.activity_id:
            await interaction.response.send_message(
                'Select an activity first.', ephemeral=True
            )
            return

        row = Activity.get(v.activity_id)
        if not row:
            await interaction.response.send_message(
                'Selected activity not found.', ephemeral=True
            )
            return

        staged_new_category = (
            v.new_category_select.values[0] if v.new_category_select.values else None
        )
        modal = ActivityEditModal(
            activity_id=v.activity_id,
            current_name=row['name'],
            current_xp=row['xp_value'],
            staged_new_category=staged_new_category,
        )
        await interaction.response.send_modal(modal)
