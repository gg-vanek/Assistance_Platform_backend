from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserRegistrationSerializer

from .permissions import IsAccountOwnerOrReadOnly
from rest_framework import response, status


class UserList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAccountOwnerOrReadOnly,)
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer


class UserRegistration(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
