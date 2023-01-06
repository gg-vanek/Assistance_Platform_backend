from django.urls import path
from .views import TaskList, TaskDetail, CreateTask, TaskApply, ApplicationDetail, TagsInfo, SubjectsInfo, \
    MyTasksList, MyApplicationsList, SetTaskDoer, ReviewOnTask

urlpatterns = [
    path('', TaskList.as_view()),
    path('<int:pk>', TaskDetail.as_view()),
    path('<int:pk>/apply', TaskApply.as_view()),
    path('<int:task>/my_application', ApplicationDetail.as_view(lookup_field='task')),
    path('<int:pk>/set_doer', SetTaskDoer.as_view()),
    # path('<int:pk>/review', ReviewOnTask.as_view()),
    # path('<int:pk>/reviews', ///.as_view()),
    path('new_task', CreateTask.as_view()),

    path('my_tasks', MyTasksList.as_view()),
    path('my_applications', MyApplicationsList.as_view()),

    # TODO возможно бесполезны => удалить
    path('tags_info', TagsInfo.as_view()),
    path('subjects_info', SubjectsInfo.as_view()),
]
