from django.urls import path

from tasks.views import TaskList, ApplicationsList, ReviewList
from .views import UserList, UserDetail, UserRegistration, UserSettings, UserProfile, UserContacts

urlpatterns = [
    path('registration', UserRegistration.as_view()),  # TODO пока сырой вариант регистрации

    path('<int:pk>', UserDetail.as_view()),  #
    path('<int:pk>/edit_settings', UserSettings.as_view()),  # настройки
    path('<int:pk>/edit_profile', UserProfile.as_view()),  # профиль
    path('<int:pk>/edit_contacts', UserContacts.as_view()),  # контакты

    path('<int:authorid>/tasks', TaskList.as_view()),  #
    path('<int:implementerid>/todo_tasks', TaskList.as_view()),  #
    path('<int:userid>/applications', ApplicationsList.as_view()),  #
    path('<int:reviewerid>/reviews', ReviewList.as_view()),  #


    path('<str:username>', UserDetail.as_view(lookup_field='username')),  # профиль юзера
    path('<str:username>/edit_settings', UserSettings.as_view(lookup_field='username')),  # настройки
    path('<str:username>/edit_profile', UserProfile.as_view(lookup_field='username')),  # профиль
    path('<str:username>/edit_contacts', UserContacts.as_view(lookup_field='username')),  # контакты

    path('<str:authorusername>/tasks', TaskList.as_view()),  # задачи где юзер-автор
    path('<str:implementerusername>/todo_tasks', TaskList.as_view()),  # задачи где юзер - исполнитель
    path('<str:username>/applications', ApplicationsList.as_view()),  # заявки пользователя по юзернейму
    path('<str:reviewerusername>/reviews', ReviewList.as_view()),  # отзывы пользователя/на пользователя по юзернейму

    path('', UserList.as_view()),  # список всех пользователей
]
