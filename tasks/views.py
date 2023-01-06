from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes

from .models import Task, Application, TaskTag, TaskSubject, TASK_STATUS_CHOICES
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCreateSerializer, TaskApplySerializer, \
    ApplicationDetailSerializer, TagInfoSerializer, SubjectInfoSerializer, ApplicationSerializer, SetTaskDoerSerializer, \
    ReviewOnTaskDetailSerializer
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


def filter_tasks_by_author(queryset, task_author, user):
    if task_author == 'me':
        queryset = queryset.filter(author=user)
    elif task_author == 'notme':
        queryset = queryset.filter(doer=user)
    elif task_author == 'both':
        queryset = queryset.filter(Q(doer=user) | Q(author=user))
    else:
        return Response({'detail': f"URL parameter task_author is '{task_author}'"
                                   f" but allowed values are 'both', 'me' and 'notme'"},
                        status=status.HTTP_400_BAD_REQUEST)

    return queryset


def filter_tasks_by_fields(queryset, tags, tags_grouping_type, task_status, difficulty_stage_of_study,
                           difficulty_course_of_study_min, difficulty_course_of_study_max, subjects):
    if tags is not None:
        if isinstance(tags, str):
            tags = tags.split(',')
        if isinstance(tags, int):
            tags = [tags]
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
        if isinstance(task_status, str):
            task_status = task_status.split(',')
        queryset = queryset.filter(status__in=task_status)
        # TODO добавить защиту от дурака, который передаст кривые статусы
        # return Response({'detail': f"URL parameter task_status is '{task_status}'"
        #                            f" but allowed values are 'A', 'P' and 'C'"},
        #                 status=status.HTTP_400_BAD_REQUEST)

    if difficulty_stage_of_study is not None:
        queryset = queryset.filter(difficulty_stage_of_study__in=difficulty_stage_of_study.split(','))
    if difficulty_course_of_study_min is not None:
        queryset = queryset.filter(difficulty_course_of_study__gte=difficulty_course_of_study_min)
    if difficulty_course_of_study_max is not None:
        queryset = queryset.filter(difficulty_course_of_study__lte=difficulty_course_of_study_max)
    if subjects is not None:
        # учитывая что у задания поле subject - единственное => выводим только через "or"
        if isinstance(subjects, str):
            subjects = subjects.split(',')
        if isinstance(subjects, int):
            subjects = [subjects]
        queryset = queryset.filter(subject__in=subjects)

    return queryset


def search_in_tasks(queryset, search_query):
    if search_query is not None:
        queryset = queryset.filter(title__icontains=search_query)
    return queryset


# выбрать одну строчку из двух.
# первая обозначает, что параметры фильтрации передаются в url_parameters
# вторая обозначает, что параметры фильтрации передаются в теле запроса
filters_location_in_request_object = 'query_params'
# filters_location_in_request_object = 'data'


def get_filtering_by_fields_params(request):
    all_filters = getattr(request, filters_location_in_request_object)
    return {'tags': all_filters.get('tags', None),
            'tags_grouping_type': all_filters.get('tags_grouping_type', 'or'),
            'task_status': all_filters.get('task_status', None),
            'difficulty_stage_of_study': all_filters.get('stage', None),
            'difficulty_course_of_study_min': all_filters.get('course_min', None),
            'difficulty_course_of_study_max': all_filters.get('course_max', None),
            'subjects': all_filters.get('subjects', None)}


def get_filtering_by_date_params(request):
    all_filters = getattr(request, filters_location_in_request_object)
    return {'date_start': all_filters.get('date_start', None),
            'date_end': all_filters.get('date_end', None),
            'date_type': all_filters.get('date_type', 'created_at')}


def get_filtering_by_author_params(request):
    all_filters = getattr(request, filters_location_in_request_object)
    return {'user': request.user,
            'task_author': all_filters.get('task_author', 'both')}


# информационные эндпоинты
# TODO TagsInfo и SubjectsInfo возможно бесполезны => удалить
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
    # TODO добавить сортировку по рейтингу автора задачи
    sort_fields = [field.name for field in Task._meta.get_fields()]

    not_for_sort_fields = ["applications", "files", "author", "doer", "description", "author_rating",
                           "review_on_author", "doer_rating", "review_on_doer", "tags"]

    for field in not_for_sort_fields:
        if field in sort_fields:
            sort_fields.remove(field)

    information_dictionary = {'tags_info': [TagInfoSerializer(tag).data for tag in TaskTag.objects.all()],
                              'subjects_info': [SubjectInfoSerializer(subject).data for subject in
                                                TaskSubject.objects.all()],
                              'filters_info': {'fields_filters': {'tags_grouping_type': ['and', 'or'],
                                                                  'tags': None,
                                                                  'task_status': TASK_STATUS_CHOICES,
                                                                  'stage': STAGE_OF_STUDY_CHOICES,
                                                                  'course_min': 0,
                                                                  'course_max': 15,
                                                                  'subjects': None},
                                               'search_filter': 'search_query',
                                               'date_filters': {'date_start': None, 'date_end': None,
                                                                'date_type': Task.datetime_fileds_names,
                                                                'date_format': '%Y-%m-%d'},
                                               'author_filters': {'task_author': ['me', 'notme', 'both']},
                                               'sort': sort_fields},
                              'profile_choices_info': {'stage_of_study_choices': STAGE_OF_STUDY_CHOICES}}

    return Response(information_dictionary)


# эндпоинты для работы с заданиями
class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()

        # фильтрация по полям
        fields_filters = get_filtering_by_fields_params(request=self.request)
        queryset = filter_tasks_by_fields(queryset, **fields_filters)
        if isinstance(queryset, Response):
            response = queryset
            return response

        # фильтрация по времени
        date_filters = get_filtering_by_date_params(request=self.request)
        queryset = filter_tasks_by_date(queryset, **date_filters)
        if isinstance(queryset, Response):
            response = queryset
            return response

        # поисковой запрос по заголовкам
        search_query = self.request.query_params.get('search_query', None)
        queryset = search_in_tasks(queryset, search_query)
        if isinstance(queryset, Response):
            response = queryset
            return response

        sort = self.request.query_params.get('sort')

        if sort is not None:
            queryset = queryset.order_by(sort)
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'tasks': serializer.data, 'filters': getattr(request, filters_location_in_request_object)})


class MyTasksList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()

        # я/не я (я исполнитель)/оба варианта
        author_filters = get_filtering_by_author_params(request=self.request)
        queryset = filter_tasks_by_author(queryset, **author_filters)
        if isinstance(queryset, Response):
            response = queryset
            return response

        # фильтрация по времени
        date_filters = get_filtering_by_date_params(request=self.request)
        queryset = filter_tasks_by_date(queryset, **date_filters)
        if isinstance(queryset, Response):
            response = queryset
            return response

        # фильтрация по различным полям у заданий
        fields_filters = get_filtering_by_fields_params(request=self.request)
        queryset = filter_tasks_by_fields(queryset, **fields_filters)
        if isinstance(queryset, Response):
            response = queryset
            return response

        # поисковой запрос по заголовкам
        search_query = self.request.query_params.get('search_query', None)
        queryset = search_in_tasks(queryset, search_query)
        if isinstance(queryset, Response):
            response = queryset
            return response

        sort = self.request.query_params.get('sort')
        if sort is not None:
            queryset = queryset.order_by(sort)

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'tasks': serializer.data, 'filters': getattr(request, filters_location_in_request_object)})


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


class ReviewOnTask(generics.RetrieveUpdateAPIView):
    # TODO create
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать doer=userID и он установится как исполнитель
    permission_classes = (permissions.IsAuthenticated, IsTaskOwnerOrReadOnly,)
    serializer_class = ReviewOnTaskDetailSerializer
    queryset = Task.objects.all()
