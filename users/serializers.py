from rest_framework import serializers

from tasks.models import Task, Application
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
    author_rating_sum = serializers.IntegerField(read_only=True)
    author_rating_count = serializers.IntegerField(read_only=True)
    doer_rating_sum = serializers.IntegerField(read_only=True)
    doer_rating_count = serializers.IntegerField(read_only=True)

    my_tasks_amount = serializers.SerializerMethodField(read_only=True)
    todo_tasks_amount = serializers.SerializerMethodField(read_only=True)
    my_applications_amount = serializers.SerializerMethodField(read_only=True)

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
                  'contact_email',
                  'contact_tg',
                  'contact_vk',
                  'author_rating_sum',
                  'author_rating_count',
                  'doer_rating_sum',
                  'doer_rating_count',
                  'my_tasks_amount',
                  'todo_tasks_amount',
                  'my_applications_amount',
                  )
        model = User

    def get_my_tasks_amount(self, user):
        all_tasks = Task.objects.filter(author=user)
        return [all_tasks.filter(status__in=['A', 'P']).count(), all_tasks.count()]

    def get_todo_tasks_amount(self, user):
        all_tasks = Task.objects.filter(doer=user)
        return [all_tasks.filter(status='P').count(), all_tasks.count()]

    def get_my_applications_amount(self, user):
        all_applications = Application.objects.filter(applicant=user)
        return [all_applications.filter(status='S').count(), all_applications.count()]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=128, write_only=True)

    class Meta:
        fields = ('username',
                  'password',
                  'email',)
        model = User

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserContactSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'contact_phone',
                  'contact_email',
                  'contact_tg',
                  'contact_vk',)
        model = User
