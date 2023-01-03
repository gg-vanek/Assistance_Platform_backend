from django.urls import path
from .views import TaskList, TaskDetail, TaskDelete, CreateTask, TaskApply, ApplicationDetail

urlpatterns = [
    path('', TaskList.as_view()),
    path('<int:pk>', TaskDetail.as_view()),
    path('<int:pk>/apply', TaskApply.as_view()),
    path('<int:task>/my_application', ApplicationDetail.as_view(lookup_field='task')),
    path('<int:pk>/delete', TaskDelete.as_view()),
    path('new_task', CreateTask.as_view())
]
