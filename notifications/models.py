from django.db import models
from django.utils import timezone

from users.models import User


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    type = models.CharField(max_length=60, default='general_notification')
    affected_object_id = models.IntegerField(default=None, blank=True, null=True)

    message = models.TextField()
    checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'notification' + str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # при переходе из статуса checked - в unchecked тоже сюда заходит
        # нельзя просто отправлять письмо на email
        print('-------------------------Создалось уведомление------------------------')
