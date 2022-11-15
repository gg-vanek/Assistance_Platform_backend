from django.urls import path
from .views import TaskList, TaskDetail, CreateTask

urlpatterns = [
    path('<int:pk>/', TaskDetail.as_view()),
    path('', TaskList.as_view()),
    path('new_task', CreateTask.as_view())
]
