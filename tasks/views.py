from rest_framework import generics, permissions

from .models import Task, Application
from .serializers import TaskDisplaySerializer, TaskUpdateSerializer, TaskCreateSerializer, TaskApplySerializer
from rest_framework.response import Response

from rest_framework import status
from rest_framework.settings import api_settings
from django.http import HttpResponse
import datetime
from .permissions import IsTaskOwnerOrReadOnly


class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskDisplaySerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = Task.objects.all()
        tags = self.request.query_params.get('tags')
        tags_grouping_type = self.request.query_params.get('tags_grouping_type', 'or')

        status = self.request.query_params.get('status')
        difficulty_stage_of_study = self.request.query_params.get('stage')
        difficulty_course_of_study = self.request.query_params.get('course')
        subjects = self.request.query_params.get('subjects')
        sort = self.request.query_params.get('sort')

        if tags is not None:
            tags = tags.split(',')
            # TODO возможно нужно переделать фильтрацию
            # типа словарик kwargs['tags__in']=tags если параметр or
            # и kwargs['четотам еще']=tags если параметр and
            if tags_grouping_type == 'or':
                # выведи задания у которых есть tag1 or tag2 etc
                queryset = queryset.filter(tags__in=tags)
            elif tags_grouping_type == 'and':
                # выведи задания у которых есть tag1 and tag2 etc
                for tag in tags:
                    queryset = queryset.filter(tags=tag)
            else:
                # TODO ошибка некорректный параметр группировки тэгов
                pass

        if status is not None:
            queryset = queryset.filter(status=status)
        if difficulty_stage_of_study is not None:
            queryset = queryset.filter(difficulty_stage_of_study=difficulty_stage_of_study)
        if difficulty_course_of_study is not None:
            queryset = queryset.filter(difficulty_course_of_study=difficulty_course_of_study)
        if subjects is not None:
            # учитывая что у задания поле subject - единственное => выводим только через "or"
            subjects = subjects.split(',')
            queryset = queryset.filter(subject__in=subjects)

        if sort is not None:
            queryset = queryset.order_by(sort)
        return queryset


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsTaskOwnerOrReadOnly,)
    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer


class TaskDelete(generics.DestroyAPIView):
    permission_classes = (IsTaskOwnerOrReadOnly,)
    queryset = Task.objects.all()


class CreateTask(generics.CreateAPIView):
    # но тут нельзя задавать "создателя задачи", "исполнителя", "статус"
    # также по умолчанию следует установить некоторые поля вроде сложности задачи
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskCreateSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
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


class TaskApply(generics.CreateAPIView):
    # TODO переделать в CreateUpdateDestroyAPIView
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskApplySerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
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
