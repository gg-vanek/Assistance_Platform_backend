from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Task, Application, TaskTag, TaskSubject, TASK_STATUS_CHOICES, Review
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCreateSerializer, TaskApplySerializer, \
    ApplicationDetailSerializer, TagInfoSerializer, SubjectInfoSerializer, ApplicationSerializer, \
    SetTaskImplementerSerializer, ReviewSerializer, CloseTaskSerializer
from rest_framework.response import Response

from rest_framework import status
import datetime
from .permissions import IsTaskOwnerOrReadOnly, IsTaskImplementerOrTaskOwner

from users.models import STAGE_OF_STUDY_CHOICES


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
                           difficulty_course_of_study_min, difficulty_course_of_study_max, subjects,
                           author_rating_min, author_rating_max):
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

    if difficulty_stage_of_study is not None:
        queryset = queryset.filter(difficulty_stage_of_study__in=difficulty_stage_of_study.split(','))
    queryset = queryset.filter(difficulty_course_of_study__gte=difficulty_course_of_study_min)
    queryset = queryset.filter(difficulty_course_of_study__lte=difficulty_course_of_study_max)

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
        queryset = queryset.filter(title__icontains=search_query)
    return queryset


# выбрать одну строчку из двух.
# первая обозначает, что параметры фильтрации передаются в url_parameters
# вторая обозначает, что параметры фильтрации передаются в теле запроса
filters_location_in_request_object = 'query_params'



def get_filtering_by_fields_params(request):
    all_filters = getattr(request, filters_location_in_request_object)
    return {'tags': all_filters.get('tags', None),
            'tags_grouping_type': all_filters.get('tags_grouping_type', 'or'),
            'task_status': all_filters.get('task_status', None),
            'difficulty_stage_of_study': all_filters.get('stage', None),
            'difficulty_course_of_study_min': all_filters.get('course_min', 0),
            'difficulty_course_of_study_max': all_filters.get('course_max', 15),
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
    sort_fields = [field.name for field in Task._meta.get_fields()]

    not_for_sort_fields = ["id", "applications", "files", "difficulty_stage_of_study", "author", "implementer",
                           "description", "tags", 'reviews']
    print(sort_fields)
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
                              'filters_info': {'fields_filters': {'tags_grouping_type': ['and', 'or'],
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


class CloseTask(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated, IsTaskOwnerOrReadOnly)
    serializer_class = CloseTaskSerializer
    queryset = Task.objects.all()


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
        if task.status != 'A':
            return Response({'detail': f"Статус задачи {task.status}. Отправка заявок на нее недоступна"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if Application.objects.filter(applicant=request.user, task=task):
            # если уже была такая заявка на это задание то ничего не меняем
            return Response({'detail': "Ваша заявка уже отправлена вы не можете добавить новую,"
                                       " но можете отредактировать старую"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        self.perform_create(serializer, data)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        return serializer.save(**data)


class SetTaskImplementer(generics.RetrieveUpdateAPIView):
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать implementer=userID и он установится как исполнитель
    permission_classes = (IsTaskOwnerOrReadOnly,)
    serializer_class = SetTaskImplementerSerializer
    queryset = Task.objects.all()


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
            return Response({'detail': f"На эту задачу так и не был назначен исполнитель. На нее нельзя оставлять отзывы"},
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

        self.perform_create(serializer, data)
        # если ошибок не выскочило, то нужно пересчитать рейтинг пользователя которому поставили отзыв
        self.update_rating(task=task, rating=request.data['rating'], review_type=data['review_type'])

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data={}):
        serializer.save(**data)

    def update_rating(self, task, rating, review_type):
        rating = int(rating)
        if review_type == 'A':
            # если ревью от автора то пересчитываем исполнителя
            implementer = task.implementer
            implementer.implementer_rating += rating
            implementer.implementer_review_counter += 1
            implementer.save()
            implementer.update_implementer_rating()

        if review_type == 'I':
            # если ревью от исполнителя то пересчитываем автора
            author = task.author
            author.author_rating += rating
            author.author_review_counter += 1
            author.save()
            author.update_author_rating()


class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    # при GET запросе возвращается список заявок
    # при пост запросе необходимо в теле запроса передать implementer=userID и он установится как исполнитель
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
        self.update_rating(task=task, review_type=review.review_type,
                           rating_delta=-review.rating,
                           counter_delta=-1)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update_rating(self, task, review_type, rating_delta, counter_delta):
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
        reviewerid = self.request.parser_context['kwargs'].get('reviewerid', None)
        reviewerusername = self.request.parser_context['kwargs'].get('reviewerusername', None)

        reviewreceiverid = self.request.parser_context['kwargs'].get('reviewreceiverid', None)
        reviewreceiverusername = self.request.parser_context['kwargs'].get('reviewreceiverusername', None)

        if reviewerid is not None:
            queryset = Review.objects.filter(reviewer__id=reviewerid)
        elif reviewerusername is not None:
            queryset = Review.objects.filter(reviewer__username=reviewerusername)

        elif reviewreceiverid is not None:
            # берем те отзывы, которые ссылаются на те задания, к которым юзер имеет отношение (автор/исполнитель)
            # но при этом откидываем из них те, которые оставил сам юзер
            # на выходе получаем только отзывы оставленные на этого юзера
            queryset = Review.objects.filter((Q(task__implementer__id=reviewreceiverid) |
                                              Q(task__author__id=reviewreceiverid)) &
                                             ~Q(reviewer__id=reviewreceiverid))
        elif reviewerusername is not None:
            # берем те отзывы, которые ссылаются на те задания, к которым юзер имеет отношение (автор/исполнитель)
            # но при этом откидываем из них те, которые оставил сам юзер
            # на выходе получаем только отзывы оставленные на этого юзера
            queryset = Review.objects.filter((Q(task__implementer__username=reviewerusername) |
                                              Q(task__author__username=reviewerusername)) &
                                             ~Q(reviewer__username=reviewerusername))
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        worst = self.request.query_params.get('worst', 0)
        best = self.request.query_params.get('best', 10)

        queryset = queryset.filter(rating__lte=best, rating__gte=worst)

        return queryset
