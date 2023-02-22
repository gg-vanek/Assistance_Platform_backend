from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q

from notifications.models import new_notification
from .models import Task, Application, TaskTag, TaskSubject, TASK_STATUS_CHOICES, Review, TaskFile
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCreateSerializer, TaskApplySerializer, \
    TagInfoSerializer, SubjectInfoSerializer, ApplicationSerializer, SetTaskImplementerSerializer, \
    ReviewSerializer, CloseTaskSerializer, AddFileSerializer
from rest_framework.response import Response

from rest_framework import status
import datetime
from .permissions import IsTaskOwnerOrReadOnly, IsTaskImplementerOrTaskOwner, IsTaskOwnerForFileWork

from users.models import STAGE_OF_STUDY_CHOICES, User


def filter_for_person(queryset, request):
    kwarg = request.parser_context['kwargs']
    kwarg_key = list(kwarg.keys())[0]
    if kwarg_key == 'authorid':
        queryset = queryset.filter(author__id=kwarg[kwarg_key])
    elif kwarg_key == 'implementerid':
        queryset = queryset.filter(implementer__id=kwarg[kwarg_key])
    elif kwarg_key == 'authorusername':
        queryset = queryset.filter(author__username=kwarg[kwarg_key])
    elif kwarg_key == 'implementerusername':
        queryset = queryset.filter(implementer__username=kwarg[kwarg_key])
    else:
        queryset = queryset.filter(~Q(author=request.user))
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


def filter_tasks_by_fields(queryset, tags, tags_grouping_type, task_status, stage_of_study,
                           course_of_study_min, course_of_study_max, subjects,
                           author_rating_min, author_rating_max):
    if tags is not None:
        if isinstance(tags, str):
            tags = tags.split(',')
        if isinstance(tags, int):
            tags = [tags]
        if tags_grouping_type == 'or':
            # выведи задания у которых есть tag1 or tag2 etc

            # distinct удаляет дубликаты заданий. В какой-то момент
            # их изза разных запросов может добавиться несколько экземпляров
            queryset = queryset.filter(tags__in=tags).distinct()
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

    if stage_of_study is not None:
        queryset = queryset.filter(stage_of_study__in=stage_of_study.split(','))
    queryset = queryset.filter(course_of_study__gte=course_of_study_min)
    queryset = queryset.filter(course_of_study__lte=course_of_study_max)

    queryset = queryset.filter(author__author_rating_normalized__gte=author_rating_min)
    queryset = queryset.filter(author__author_rating_normalized__lte=author_rating_max)

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
        queryset = queryset.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
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
            'task_status': all_filters.get('task_status', None if list(request.parser_context['kwargs'].keys())[0] else 'A'),
            'stage_of_study': all_filters.get('stage', None),
            'course_of_study_min': all_filters.get('course_min', 0),
            'course_of_study_max': all_filters.get('course_max', 15),
            'subjects': all_filters.get('subjects', None),
            'author_rating_min': all_filters.get('author_rating_min', 0),
            'author_rating_max': all_filters.get('author_rating_max', 10)}


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
    sort_fields = [field.name for field in Task._meta.get_fields()] + ['author_rating']

    not_for_sort_fields = ["id", "applications", "files", "stage_of_study", "author", "implementer",
                           "status", "description", "tags", 'reviews']
    print(sort_fields)
    for field in not_for_sort_fields:
        if field in sort_fields:
            sort_fields.remove(field)

    sort_fields_names = {'title': 'Название',
                         'course_of_study': 'Класс/курс обучения',
                         'subject': 'Предмет',
                         'created_at': 'Дата создания',
                         'updated_at': 'Дата последнего редактирования',
                         'stop_accepting_applications_at': 'Дата планируемого окончания приема заявок',
                         'expires_at': 'Дата планируемого закрытия задачи',
                         'closed_at': 'Дата закрытия задачи',
                         'price': 'Вознаграждение за решение',
                         'author_rating': 'Рейтинг автора задачи'}

    sort_fields_info = {}
    for sort_field in sort_fields:
        if sort_field in sort_fields_names:
            sort_fields_info[sort_field] = sort_fields_names[sort_field]
        else:
            sort_fields_info[sort_field] = sort_field

    information_dictionary = {'tags_info': [TagInfoSerializer(tag).data for tag in TaskTag.objects.all()],
                              'subjects_info': [SubjectInfoSerializer(subject).data for subject in
                                                TaskSubject.objects.all()],
                              'task_filters_info': {'fields_filters': {'tags_grouping_type': ['and', 'or'],
                                                                       'tags': None,
                                                                       'task_status': TASK_STATUS_CHOICES,
                                                                       'stage': STAGE_OF_STUDY_CHOICES,
                                                                       'course_min': 0,
                                                                       'course_max': 15,
                                                                       'subjects': None,
                                                                       'author_rating_min': 0,
                                                                       'author_rating_max': 10},
                                                    'search_filter': 'search_query',
                                                    'date_filters': {'date_start': None, 'date_end': None,
                                                                     'date_type': Task.datetime_fileds_names,
                                                                     'date_format': '%Y-%m-%d'},
                                                    'sort': sort_fields_info},

                              'reviews_filters_info': {'fields_filters': {'review_type': ['all', 'send', 'received'],
                                                                          'rating_min': 0,
                                                                          'rating_max': 10},
                                                       'date_filters': {'date_start': None, 'date_end': None,
                                                                        'date_format': '%Y-%m-%d'}
                                                       },

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
        if sort is not None and sort != '-':
            if sort.endswith('author_rating'):
                sort = sort.replace('author_rating', 'author__author_rating_normalized')
            queryset = queryset.order_by(sort)
        return queryset

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
        if req_data.get('stage_of_study') == 'N' or 'stage_of_study' not in req_data:
            req_data['stage_of_study'] = request.user.stage_of_study
        if req_data.get('course_of_study') == '0' or 'course_of_study' not in req_data:
            req_data['course_of_study'] = request.user.course_of_study

        serializer = self.get_serializer(data=req_data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer, data)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        serializer.save(**data)


class CloseTask(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated, IsTaskOwnerOrReadOnly)
    serializer_class = CloseTaskSerializer
    queryset = Task.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(task, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            task._prefetched_objects_cache = {}

        if task.implementer:
            new_notification(user=task.implementer,
                             type='closed_task_notification',
                             affected_object_id=task.id,
                             message=f"Автор задания {task.id} закрыл его. Вы можете оставить отзыв.",
                             checked=0)

        return Response(serializer.data)


class AddFile(generics.CreateAPIView):
    permission_classes = (IsTaskOwnerForFileWork,)
    serializer_class = AddFileSerializer


class DeleteFile(generics.DestroyAPIView):
    permission_classes = (IsTaskOwnerForFileWork,)

    def get_object(self):
        task = Task.objects.get(id=self.request.parser_context['kwargs'].get('pk', None))
        file = TaskFile.objects.get(id=self.request.query_params['file_id'])
        if file.task != task:
            return Response({'detail': f"Файл который вы пытаетесь удалить относится к другому заданию"})

        return file


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

        # отсортировать заявки по "рейтингу исполнителя" среди подавших заявки
        queryset = queryset.order_by('-applicant__implementer_rating_normalized')

        return queryset


class ApplicationDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplicationSerializer

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
        if task.status != 'A':
            return Response({'detail': f"Статус задачи {task.status}. Отправка заявок на нее недоступна"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if Application.objects.filter(applicant=request.user, task=task):
            # если уже была такая заявка на это задание то ничего не меняем
            return Response({'detail': "Ваша заявка уже отправлена вы не можете добавить новую,"
                                       " но можете отредактировать старую"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        application = self.perform_create(serializer, data)
        headers = self.get_success_headers(serializer.data)

        new_notification(user=task.author,
                         type='application_notification',
                         affected_object_id=task.id,
                         message=f"На ваше задание {task.id} отправлена новая заявка",
                         checked=0)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        return serializer.save(**data)


class SetTaskImplementer(generics.RetrieveUpdateAPIView):
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать implementer=userID и он установится как исполнитель
    permission_classes = (IsTaskOwnerOrReadOnly,)
    serializer_class = SetTaskImplementerSerializer
    queryset = Task.objects.all()
    # уведомления отправляются через сериализатор


# работа с отзывами
class CreateReview(generics.CreateAPIView):
    permission_classes = (IsTaskImplementerOrTaskOwner,)
    serializer_class = ReviewSerializer

    def create(self, request, *args, **kwargs):
        task = Task.objects.get(pk=request.parser_context['kwargs']['pk'])
        if task.status != 'C':
            return Response({'detail': f"Создатель задачи еще не закрыл ее. Вы не можете оставить отзыв"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif not task.implementer:
            return Response(
                {'detail': f"На эту задачу так и не был назначен исполнитель. На нее нельзя оставлять отзывы"},
                status=status.HTTP_400_BAD_REQUEST)
        elif Review.objects.filter(task=task, reviewer=request.user):
            return Response({'detail': f"Вы уже оставляли отзыв на эту задачу. Вы можете отредактировать старый"},
                            status=status.HTTP_400_BAD_REQUEST)
        data = {}
        data['reviewer'] = request.user
        data['task'] = task
        if task.author == request.user:
            data['review_type'] = 'A'
        elif task.implementer == request.user:
            data['review_type'] = 'I'
        else:
            # если не исполнитель и не создатель, то че за нах
            return Response({'detail': f"Похоже вы не можете оставить отзыв на эту задачу"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = self.perform_create(serializer, data)
        # если ошибок не выскочило, то нужно пересчитать рейтинг пользователя которому поставили отзыв
        update_rating(task=task, review_type=data['review_type'],
                      rating_delta=request.data['rating'],
                      counter_delta=1)

        headers = self.get_success_headers(serializer.data)

        # если все прошло хорошо и до сих пор нет ошибок, то отправить уведомления
        if review.task.author == review.reviewer:
            receiver = review.task.implementer
        elif review.task.implementer == review.reviewer:
            receiver = review.task.author

        # notification_to_receiver
        new_notification(user=receiver,
                         type='review_notification',
                         affected_object_id=review.task.id,
                         message=f"Был оставлен отзыв о вас по заданию {review.task.id}",
                         checked=0)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        return serializer.save(**data)


class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewSerializer

    def get_object(self):
        task = Task.objects.get(id=self.request.parser_context['kwargs']['pk'])
        return Review.objects.get(task=task, reviewer=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        review = self.get_object()

        task = Task.objects.get(pk=request.parser_context['kwargs']['pk'])
        old_rating = review.rating
        new_rating = request.data['rating']

        serializer = self.get_serializer(review, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        self.update_rating(task=task, review_type=review.review_type,
                           rating_delta=int(new_rating) - old_rating,
                           counter_delta=0)

        if getattr(review, '_prefetched_objects_cache', None):
            review._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        task = Task.objects.get(pk=request.parser_context['kwargs']['pk'])

        review = self.get_object()
        self.perform_destroy(review)
        update_rating(task=task, review_type=review.review_type,
                      rating_delta=-review.rating,
                      counter_delta=-1)

        return Response(status=status.HTTP_204_NO_CONTENT)


def update_rating(task, review_type, rating_delta, counter_delta):
    if review_type == 'A':
        # если ревью от автора то пересчитываем исполнителя
        implementer = task.implementer
        implementer.implementer_rating += rating_delta
        implementer.implementer_review_counter += counter_delta
        implementer.save()
        implementer.update_implementer_rating()

    if review_type == 'I':
        # если ревью от исполнителя то пересчитываем автора
        author = task.author
        author.author_rating += rating_delta
        author.author_review_counter += counter_delta
        author.save()
        author.update_author_rating()


class ReviewList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewSerializer

    def get_queryset(self):
        userid = self.request.parser_context['kwargs'].get('reviewerid', None)
        username = self.request.parser_context['kwargs'].get('reviewerusername', None)

        query_params = getattr(self.request, 'query_params')
        review_type = query_params.get('review_type', 'all')  # send/received
        date_start = query_params.get('date_start', None)
        date_end = query_params.get('date_end', None)
        rating_min = query_params.get('rating_min', 0)
        rating_max = query_params.get('rating_max', 10)

        if userid is not None:
            user = User.objects.get(id=userid)
        elif username is not None:
            user = User.objects.get(username=username)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        queryset = Review.objects.filter(Q(task__implementer=user) |
                                         Q(task__author=user))

        if review_type != 'all':
            if review_type == 'send':
                queryset = queryset.filter(reviewer=user)
            elif review_type == 'received':
                queryset = queryset.filter(~Q(reviewer=user))

        if date_start is not None:
            queryset = queryset.filter(created_at__gte=date_start)
        if date_end is not None:
            queryset = queryset.filter(created_at__lte=date_end)

        queryset = queryset.filter(rating__gte=rating_min, rating__lte=rating_max)

        return queryset
