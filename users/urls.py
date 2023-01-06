from django.urls import path

from tasks.views import TaskList, MyApplicationsList
from .views import UserList, UserDetail, UserRegistration, CurrentUserDetail

urlpatterns = [
    path('registration', UserRegistration.as_view()),  # TODO пока сырой вариант
    path('my_profile', CurrentUserDetail.as_view()),


    path('<int:pk>', UserDetail.as_view()),
    path('<int:authorid>/tasks', TaskList.as_view()),
    path('<int:doerid>/todo_tasks', TaskList.as_view()),
    path('<int:userid>/my_applications', MyApplicationsList.as_view()),

    path('<str:username>', UserDetail.as_view(lookup_field='username')),
    path('<str:authorusername>/tasks', TaskList.as_view()),
    path('<str:doerusername>/todo_tasks', TaskList.as_view()),
    path('<str:username>/my_applications', MyApplicationsList.as_view()),

    path('', UserList.as_view()),
]
