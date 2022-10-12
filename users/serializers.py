from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('username',
                  'email',
                  'first_name',
                  'last_name',
                  'age',
                  'stage_of_study',
                  'course_of_study',
                  'biography',)
        model = CustomUser
