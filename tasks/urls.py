from django.urls import path
from .views import TaskList, TaskDetail, TaskDelete, CreateTask

urlpatterns = [
    path('', TaskList.as_view()),
    path('<int:pk>/', TaskDetail.as_view()),
    path('<int:pk>/delete', TaskDelete.as_view()),
    path('new_task', CreateTask.as_view())
]
