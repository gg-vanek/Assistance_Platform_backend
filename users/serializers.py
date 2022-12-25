from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'email',)
        model = User


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'email',
                  'profile_image',
                  'biography',
                  'stage_of_study',
                  'course_of_study',
                  'contact_phone',
                  'contact_email',)
        model = User
