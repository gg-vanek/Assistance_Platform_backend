from django.urls import path
from .views import TaskList, TaskDetail

urlpatterns = [
    path('<int:pk>/', TaskDetail.as_view()),
    path('', TaskList.as_view()),
]
