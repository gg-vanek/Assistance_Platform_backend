from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import UserSerializer

from .permissions import IsAccountOwnerOrReadOnly


class UserList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAccountOwnerOrReadOnly,)
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
