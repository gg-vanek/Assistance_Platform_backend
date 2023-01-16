from django.urls import path
from .views import TaskList, TaskDetail, CreateTask, TaskApply, ApplicationDetail, SetTaskImplementer, CloseTask, \
    CreateReview, ReviewDetail

urlpatterns = [
    path('', TaskList.as_view()),
    path('<int:pk>', TaskDetail.as_view()),
    path('<int:pk>/apply', TaskApply.as_view()),
    path('<int:pk>/set_implementer', SetTaskImplementer.as_view()),
    path('<int:task>/my_application', ApplicationDetail.as_view(lookup_field='task')),
    path('<int:pk>/close_task', CloseTask.as_view()),

    path('<int:pk>/new_review', CreateReview.as_view()),  # эндпоинт для оставления отзыва
    path('<int:pk>/my_review', ReviewDetail.as_view()),  # эндпоинт для просмотра отзывов? для списка отзывов?
    path('new_task', CreateTask.as_view()),
]
