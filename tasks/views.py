from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes

from .models import Task, Application, TaskTag, TaskSubject
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCreateSerializer, TaskApplySerializer, \
    ApplicationDetailSerializer, TagInfoSerializer, SubjectInfoSerializer, ApplicationSerializer, SetTaskDoerSerializer
from rest_framework.response import Response

from rest_framework import status
from rest_framework.settings import api_settings
from django.http import HttpResponse
import datetime
from .permissions import IsTaskOwnerOrReadOnly

from users.models import STAGE_OF_STUDY_CHOICES


def filter_tasks_by_date(queryset, date_start, date_end, date_type):
    date_filtering_dict = {}
    if date_start is not None:
        date_filtering_dict[date_type + '__gte'] = date_start
    if date_end is not None:
        date_filtering_dict[date_type + '__lte'] = date_end

    if date_filtering_dict:
        # TODO добавить защиту от дурака, который передаст кривую дату
        queryset = queryset.filter(**date_filtering_dict)

    return queryset


def filter_tasks_by_fields(queryset, tags, tags_grouping_type, task_status, difficulty_stage_of_study,
                           difficulty_course_of_study, subjects):
    if tags is not None:
        tags = tags.split(',')
        if tags_grouping_type == 'or':
            # выведи задания у которых есть tag1 or tag2 etc
            queryset = queryset.filter(tags__in=tags)
        elif tags_grouping_type == 'and':
            # выведи задания у которых есть tag1 and tag2 etc
            for tag in tags:
                queryset = queryset.filter(tags=tag)
        else:
            return Response({'detail': f"URL parameter tags_grouping_type is '{tags_grouping_type}'"
                                       f" but allowed values are 'and' and 'or'"},
                            status=status.HTTP_400_BAD_REQUEST)

    if task_status is not None:
        task_status = task_status.split(',')
        queryset = queryset.filter(status__in=task_status)
        # TODO добавить защиту от дурака, который передаст кривые статусы
        # return Response({'detail': f"URL parameter task_status is '{task_status}'"
        #                            f" but allowed values are 'A', 'P' and 'C'"},
        #                 status=status.HTTP_400_BAD_REQUEST)

    if difficulty_stage_of_study is not None:
        queryset = queryset.filter(difficulty_stage_of_study=difficulty_stage_of_study)
    if difficulty_course_of_study is not None:
        queryset = queryset.filter(difficulty_course_of_study=difficulty_course_of_study)
    if subjects is not None:
        # учитывая что у задания поле subject - единственное => выводим только через "or"
        subjects = subjects.split(',')
        queryset = queryset.filter(subject__in=subjects)

    return queryset


def search_in_tasks(queryset, search_query):
    if search_query is not None:
        queryset = queryset.filter(title__contains=search_query)
    return queryset


# информационные эндпоинты
class TagsInfo(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TagInfoSerializer
    queryset = TaskTag.objects.all()


class SubjectsInfo(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SubjectInfoSerializer
    queryset = TaskSubject.objects.all()


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def informational_endpoint_view(request):
    information_dictionary = {'tags_info': [TagInfoSerializer(tag).data for tag in TaskTag.objects.all()],
                              'subjects_info': [SubjectInfoSerializer(subject).data for subject in
                                                TaskSubject.objects.all()],
                              'filters_info': {'fields_filters': '...',
                                               'search_filter': '...',
                                               'date_filters': '...',
                                               'author_filters': '...'},
                              'profile_choices_info': {'stage_of_study_choices': STAGE_OF_STUDY_CHOICES}}

    return Response(information_dictionary)


# эндпоинты для работы с заданиями
class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()

        # фильтрация по полям
        fields_filters = {'tags': self.request.query_params.get('tags', None),
                          'tags_grouping_type': self.request.query_params.get('tags_grouping_type', 'or'),
                          'task_status': self.request.query_params.get('task_status', None),
                          'difficulty_stage_of_study': self.request.query_params.get('stage', None),
                          'difficulty_course_of_study': self.request.query_params.get('course', None),
                          'subjects': self.request.query_params.get('subjects', None)}
        queryset = filter_tasks_by_fields(queryset, **fields_filters)

        # фильтрация по времени
        date_filters = {'date_start': self.request.query_params.get('date_start', None),
                        'date_end': self.request.query_params.get('date_end', None),
                        'date_type': self.request.query_params.get('date_type', 'created_at')}
        queryset = filter_tasks_by_date(queryset, **date_filters)

        # поисковой запрос по заголовкам
        search_query = self.request.query_params.get('search_query', None)
        queryset = search_in_tasks(queryset, search_query)

        sort = self.request.query_params.get('sort')

        if sort is not None:
            queryset = queryset.order_by(sort)
        return queryset


class MyTasksList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()

        # я/не я (я исполнитель)/оба варианта
        task_author = self.request.query_params.get('task_author', 'both')

        if task_author == 'me':
            queryset = queryset.filter(author=self.request.user)
        elif task_author == 'notme':
            queryset = queryset.filter(doer=self.request.user)
        elif task_author == 'both':
            queryset = queryset.filter(Q(doer=self.request.user) | Q(author=self.request.user))
        else:
            return Response({'detail': f"URL parameter task_author is '{task_author}'"
                                       f" but allowed values are 'both', 'me' and 'notme'"},
                            status=status.HTTP_400_BAD_REQUEST)

        # фильтрация по времени
        date_filters = {'date_start': self.request.query_params.get('date_start', None),
                        'date_end': self.request.query_params.get('date_end', None),
                        'date_type': self.request.query_params.get('date_type', 'created_at')}
        queryset = filter_tasks_by_date(queryset, **date_filters)

        # фильтрация по различным полям у заданий
        fields_filters = {'tags': self.request.query_params.get('tags', None),
                          'tags_grouping_type': self.request.query_params.get('tags_grouping_type', 'or'),
                          'task_status': self.request.query_params.get('task_status', None),
                          'difficulty_stage_of_study': self.request.query_params.get('stage', None),
                          'difficulty_course_of_study': self.request.query_params.get('course', None),
                          'subjects': self.request.query_params.get('subjects', None)}
        queryset = filter_tasks_by_fields(queryset, **fields_filters)

        # поисковой запрос по заголовкам
        search_query = self.request.query_params.get('search_query', None)
        queryset = search_in_tasks(queryset, search_query)

        sort = self.request.query_params.get('sort')
        if sort is not None:
            queryset = queryset.order_by(sort)

        return queryset


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsTaskOwnerOrReadOnly,)
    queryset = Task.objects.all()
    serializer_class = TaskDetailSerializer


class CreateTask(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskCreateSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # TODO возможно нужно полностью перенести в метод create у сериализатора
        req_data = request.data.copy()
        data = {'author': request.user,
                'status': 'A',
                'created_at': datetime.datetime.now(),
                'updated_at': datetime.datetime.now(),
                'expires_at': datetime.datetime.now() + datetime.timedelta(days=7)}

        if req_data.get('stop_accepting_applications_at') == '' or 'stop_accepting_applications_at' not in req_data:
            req_data['stop_accepting_applications_at'] = datetime.datetime.now() + datetime.timedelta(days=7)
        if req_data.get('difficulty_stage_of_study') == 'N' or 'difficulty_stage_of_study' not in req_data:
            req_data['difficulty_stage_of_study'] = request.user.stage_of_study
        if req_data.get('difficulty_course_of_study') == '0' or 'difficulty_course_of_study' not in req_data:
            req_data['difficulty_course_of_study'] = request.user.course_of_study

        serializer = self.get_serializer(data=req_data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer, data)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        serializer.save(**data)


# эндпоинты для работы с заявками
class MyApplicationsList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        queryset = Application.objects.filter(applicant=self.request.user)
        application_status = self.request.query_params.get('application_status', None)
        if application_status is not None:
            application_status = application_status.split(',')
            queryset = queryset.filter(status__in=application_status)

        return queryset


class ApplicationDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplicationDetailSerializer

    def get_queryset(self):
        queryset = Application.objects.all()
        queryset = queryset.filter(applicant=self.request.user)
        return queryset


class TaskApply(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskApplySerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # перенести в метод create у сериализатора
        req_data = request.data.copy()
        task = Task.objects.get(pk=kwargs['pk'])

        data = {'applicant': request.user,
                'task': task,
                'created_at': datetime.datetime.now(),
                'updated_at': datetime.datetime.now(), }

        serializer = self.get_serializer(data=req_data)
        serializer.is_valid(raise_exception=True)

        if request.user == task.author:
            return Response({'detail': "Cоздатель задачи не может быть ее исполнителем"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if any([application.applicant == request.user for application in task.applications.all()]):
            # если уже была такая заявка на это задание то ничего не меняем
            return Response({'detail': "Ваша заявка уже принята вы не можете добавить новую,"
                                       " но можете отредактировать старую"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        self.perform_create(serializer, data)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        return serializer.save(**data)


class SetTaskDoer(generics.RetrieveUpdateAPIView):
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать doer=userID и он установится как исполнитель
    permission_classes = (permissions.IsAuthenticated, IsTaskOwnerOrReadOnly,)
    serializer_class = SetTaskDoerSerializer
    queryset = Task.objects.all()
