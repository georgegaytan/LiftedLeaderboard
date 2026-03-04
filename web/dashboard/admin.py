from django.contrib import admin

from .models import Activity, ActivityRecord, LevelThreshold, User

admin.site.register(User)
admin.site.register(Activity)
admin.site.register(ActivityRecord)
admin.site.register(LevelThreshold)
