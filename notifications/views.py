from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationList(generics.ListAPIView, generics.UpdateAPIView):
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

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"notifications": serializer.data, "new": queryset.filter(checked=False).count()})

    def put(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        for notification in queryset:
            notification.checked = True
            notification.save()

        return Response(status=status.HTTP_202_ACCEPTED)
