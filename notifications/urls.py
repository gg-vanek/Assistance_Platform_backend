from django.urls import path
from .views import NotificationList

urlpatterns = [
    path('', NotificationList.as_view()),
]
