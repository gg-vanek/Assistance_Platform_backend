from rest_framework import generics, permissions
from .models import Task
from .serializers import TaskSerializer
from rest_framework.response import Response

from .permissions import IsTaskOwnerOrReadOnly


class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TaskSerializer

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

        return queryset



class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsTaskOwnerOrReadOnly,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
