from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer, UserDetailSerializer

from .permissions import IsAccountOwnerOrReadOnly


class UserList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAccountOwnerOrReadOnly,)
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
