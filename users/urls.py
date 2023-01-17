from django.urls import path

from tasks.views import TaskList, ApplicationsList, ReviewList
from .views import UserList, UserDetail, UserRegistration, CurrentUserDetail

urlpatterns = [
    path('registration', UserRegistration.as_view()),  # TODO пока сырой вариант регистрации

    path('<int:pk>', UserDetail.as_view()),  #
    path('<int:authorid>/tasks', TaskList.as_view()),  #
    path('<int:implementerid>/todo_tasks', TaskList.as_view()),  #
    path('<int:userid>/applications', ApplicationsList.as_view()),  #
    path('<int:userid>/my_reviews', ReviewList.as_view()),  #

    path('<str:username>', UserDetail.as_view(lookup_field='username')),  # профиль юзер (со всей хуйней)
    path('<str:authorusername>/tasks', TaskList.as_view()),  # задачи где юзер-автор
    path('<str:implementerusername>/todo_tasks', TaskList.as_view()),  # задачи где юзер - исполнитель
    path('<str:username>/applications', ApplicationsList.as_view()),  # заявки пользователя по юзернейму
    path('<str:username>/my_reviews', ReviewList.as_view()),  # отзывы пользователя по юзернейму

    path('', UserList.as_view()),  # список всех пользователей
]
