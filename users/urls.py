from django.urls import path
from .views import UserList, UserDetail, UserRegistration, CurrentUserDetail

urlpatterns = [
    path('registration', UserRegistration.as_view()),
    path('my_profile', CurrentUserDetail.as_view()),
    path('<int:pk>', UserDetail.as_view()),
    path('<str:username>', UserDetail.as_view(lookup_field='username')),
    path('', UserList.as_view()),
]
