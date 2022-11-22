from rest_framework import generics, permissions
from .models import Task
from .serializers import TaskDisplaySerializer, TaskUpdateSerializer, TaskCreateSerializer
from rest_framework.response import Response

from rest_framework import status
from rest_framework.settings import api_settings
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse

import datetime

from .permissions import IsTaskOwnerOrReadOnly


def ApplyForTask(request, pk):
    try:
        task = Task.objects.get(task_id=pk)

        if request.user == task.author:
            # вывести "создатель задачи не может быть ее исполнителем"
            html = "<html><body>Ошибка: Cоздатель задачи не может быть ее исполнителем</body></html>"
            return HttpResponse(html)
        if task.applicants.filter(pk=request.user.pk).exists():
            html = "<html><body>Ошибка: вы уже подали заявку на эту задачу</body></html>"
            return HttpResponse(html)

        task.applicants.add(request.user.pk)
        task.save()
        return HttpResponse("<html><body>ваша заявка отправлена</body></html>")

    except ObjectDoesNotExist:
        return HttpResponseNotFound("<h2>Task not found</h2>")



class ChooseDoer():
    # TODO: при запросе от владельца задачи задавать решателя задачи и менять статус задачи
    pass


class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskDisplaySerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = Task.objects.all()
        tags = self.request.query_params.get('tag')
        status = self.request.query_params.get('status')
        difficulty_stage_of_study = self.request.query_params.get('stage')
        difficulty_course_of_study = self.request.query_params.get('course')
        subject = self.request.query_params.get('subject')
        sort = self.request.query_params.get('sort')

        if tags is not None:
            for tag in tags.split(','):
                queryset = queryset.filter(tags=tag)
        if status is not None:
            queryset = queryset.filter(status=status)
        if difficulty_stage_of_study is not None:
            queryset = queryset.filter(difficulty_stage_of_study=difficulty_stage_of_study)
        if difficulty_course_of_study is not None:
            queryset = queryset.filter(difficulty_course_of_study=difficulty_course_of_study)
        if subject is not None:
            queryset = queryset.filter(subject=subject)

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
                'status': 'accepting applications',
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
