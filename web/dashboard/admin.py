from django.contrib import admin

from .models import Activity, ActivityRecord, LevelThreshold, User

class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('last_login',)
    list_display = ('display_name', 'email', 'level', 'total_xp', 'is_admin')

admin.site.register(User, UserAdmin)
admin.site.register(Activity)
admin.site.register(ActivityRecord)
admin.site.register(LevelThreshold)
