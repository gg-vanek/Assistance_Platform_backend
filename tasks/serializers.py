from rest_framework import serializers

from users.models import CustomUser
from .models import Task, Application


class TaskApplySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('message',)
        model = Application


class TaskDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('task_id',
                  'list_applicants',
                  'author',
                  'doer',
                  'title',
                  'difficulty_stage_of_study',
                  'difficulty_course_of_study',
                  'tags',
                  'subject',
                  'description',
                  'status',
                  'created_at',
                  'updated_at',
                  'stop_accepting_applications_at',
                  'expires_at')
        model = Task


class TaskUpdateSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        fields = ('author',
                  'title',
                  'difficulty_stage_of_study',
                  'difficulty_course_of_study',
                  'tags',
                  'subject',
                  'description',
                  'stop_accepting_applications_at')
        model = Task


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('title',
                  'difficulty_stage_of_study',
                  'difficulty_course_of_study',
                  'tags',
                  'subject',
                  'description',
                  'stop_accepting_applications_at')
        model = Task
