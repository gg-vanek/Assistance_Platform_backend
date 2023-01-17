from django.contrib import admin

from notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ('user',
                    'type',
                    'affected_object_id',
                    'message',
                    'checked',
                    'created_at')


# Register your models here.
admin.site.register(Notification, NotificationAdmin)
