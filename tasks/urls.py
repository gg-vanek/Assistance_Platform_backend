from django.urls import path
from .views import TaskList, TaskDetail, CreateTask, TaskApply, ApplicationDetail, SetTaskDoer, ReviewOnTask

urlpatterns = [
    path('', TaskList.as_view()),
    path('<int:pk>', TaskDetail.as_view()),
    path('<int:pk>/apply', TaskApply.as_view()),
    path('<int:pk>/set_doer', SetTaskDoer.as_view()),
    path('<int:task>/my_application', ApplicationDetail.as_view(lookup_field='task')),

    # path('<int:pk>/review', ReviewOnTask.as_view()), # эндпоинт для оставления отзыва
    # path('<int:pk>/reviews', ///.as_view()), # эндпоинт для просмотра отзывов? для списка отзывов?
    path('new_task', CreateTask.as_view()),
]
