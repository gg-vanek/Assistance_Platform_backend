from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied

from .models import Task, Application, TaskTag, TaskSubject, TASK_STATUS_CHOICES
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCreateSerializer, TaskApplySerializer, \
    ApplicationDetailSerializer, TagInfoSerializer, SubjectInfoSerializer, ApplicationSerializer, SetTaskDoerSerializer, \
    ReviewOnTaskDetailSerializer
from rest_framework.response import Response

from rest_framework import status
from rest_framework.settings import api_settings
from django.http import Http404, HttpResponseForbidden
import datetime
from .permissions import IsTaskOwnerOrReadOnly

from users.models import STAGE_OF_STUDY_CHOICES


def filter_for_person(queryset, request):
    kwarg = request.parser_context['kwargs']
    kwarg_key = list(kwarg.keys())[0]
    if kwarg_key == 'authorid':
        queryset = queryset.filter(author__id=kwarg[kwarg_key])
    elif kwarg_key == 'doerid':
        queryset = queryset.filter(doer__id=kwarg[kwarg_key])
    elif kwarg_key == 'authorusername':
        queryset = queryset.filter(author__username=kwarg[kwarg_key])
    elif kwarg_key == 'doerusername':
        queryset = queryset.filter(doer__username=kwarg[kwarg_key])
    else:
        pass
    return queryset


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


# информационные эндпоинты
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def informational_endpoint_view(request):
    # TODO добавить сортировку по рейтингу автора задачи
    sort_fields = [field.name for field in Task._meta.get_fields()]

    not_for_sort_fields = ["id", "applications", "files", "difficulty_stage_of_study", "author", "doer", "description",
                           "author_rating", "review_on_author", "doer_rating", "review_on_doer", "tags"]

    for field in not_for_sort_fields:
        if field in sort_fields:
            sort_fields.remove(field)

    sort_fields_names = {'title': 'Название',
                         'difficulty_course_of_study': 'Класс/курс обучения',
                         'subject': 'Предмет',
                         'status': 'Статус задачи',
                         'created_at': 'Дата создания',
                         'updated_at': 'Дата последнего редактирования',
                         'stop_accepting_applications_at': 'Дата планируемого окончания рпиема заявок',
                         'expires_at': 'Дата планируемого закрытия задачи',
                         'closed_at': 'Дата закрытия задачи',
                         'price': 'Вознаграждение за решение'}

    sort_fields_info = {}
    for sort_field in sort_fields:
        if sort_field in sort_fields_names:
            sort_fields_info[sort_field] = sort_fields_names[sort_field]
        else:
            sort_fields_info[sort_field] = sort_field

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
                                               'sort': sort_fields_info},
                              'profile_choices_info': {'stage_of_study_choices': STAGE_OF_STUDY_CHOICES}}

    return Response(information_dictionary)


# эндпоинты для работы с заданиями
class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()
        if self.request.parser_context['kwargs']:
            queryset = filter_for_person(queryset, self.request)

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
class ApplicationsList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        userid = self.request.parser_context['kwargs'].get('userid', None)
        username = self.request.parser_context['kwargs'].get('username', None)

        if userid is not None and (self.request.user.id == userid or self.request.user.is_staff):
            queryset = Application.objects.filter(applicant__id=userid)

        elif username is not None and (self.request.user.username == username or self.request.user.is_staff):
            queryset = Application.objects.filter(applicant__username=username)
        else:
            raise PermissionDenied()
        application_status = self.request.query_params.get('application_status', None)
        if application_status is not None and not isinstance(queryset, list):
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


# работа с отзывами
class ReviewOnTask(generics.RetrieveUpdateAPIView):
    # TODO create
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать doer=userID и он установится как исполнитель
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewOnTaskDetailSerializer
    queryset = Task.objects.all()
