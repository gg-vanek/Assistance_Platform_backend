from django.urls import path
from .views import TaskList, TaskDetail, CreateTask, TaskApply, ApplicationDetail, SetTaskImplementer, CloseTask, \
    CreateReview, ReviewDetail

urlpatterns = [
    path('', TaskList.as_view()),  # список заданий
    path('<int:pk>', TaskDetail.as_view()),  # задание по индексу подробно
    path('<int:pk>/apply', TaskApply.as_view()),  # подача заявки на задачу
    path('<int:pk>/set_implementer', SetTaskImplementer.as_view()),  # назначение исполнителя на задачу
    path('<int:task>/my_application', ApplicationDetail.as_view(lookup_field='task')),
    # просмотр отправленной текущим юзером заявки
    path('<int:pk>/close_task', CloseTask.as_view()),
    # перевод задания из любого статуса в статус "закрыта" (делает автор задачи)

    path('<int:pk>/new_review', CreateReview.as_view()),  # эндпоинт для оставления отзыва
    path('<int:pk>/my_review', ReviewDetail.as_view()),  # эндпоинт для просмотра отзыва от текущего пользователя

    path('new_task', CreateTask.as_view()),  # создание новой задачи
]
