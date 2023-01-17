from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('user',
                  'type',
                  'affected_object_id',
                  'message',
                  'checked',
                  'created_at',)
        model = Notification