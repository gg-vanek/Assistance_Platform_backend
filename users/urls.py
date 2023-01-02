from django.urls import path
from .views import UserList, UserDetail

urlpatterns = [
    path('<int:pk>', UserDetail.as_view()),
    path('<str:username>', UserDetail.as_view(lookup_field='username')),
    path('', UserList.as_view()),
]
