from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer


class NotificationList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        notification_type = getattr(self.request, 'query_params').get('notification_type', None)

        if notification_type == 'new':
            queryset = queryset.filter(checked=0)
        elif notification_type == 'old':
            queryset = queryset.filter(checked=1)
        else:
            pass

        for notification in queryset:
            notification.checked = True
            notification.save()

        return queryset

