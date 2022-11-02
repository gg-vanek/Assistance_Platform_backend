from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('task_id',
                  'title',
                  'difficulty_stage_of_study',
                  'difficulty_course_of_study',
                  'get_tags',
                  'subject',
                  'description',
                  'status',
                  'created_at',
                  'stop_accepting_applications_at',
                  'expires_at')
        model = Task
