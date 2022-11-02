from rest_framework import generics, permissions
from .models import Task
from .serializers import TaskSerializer

from .permissions import IsTaskOwnerOrReadOnly


class TaskList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsTaskOwnerOrReadOnly,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
