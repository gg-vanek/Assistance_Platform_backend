from rest_framework import serializers

from users.models import User
from .models import Task, Application


class TaskApplySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('message',)
        model = Application


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant = serializers.CharField(source='applicant.username', read_only=True)
    task = serializers.CharField(source='task.id', read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

    class Meta:
        fields = ('id', 'applicant', 'task', 'message', 'created_at', 'updated_at',)
        model = Application


class TaskSerializer(serializers.ModelSerializer):
    applicants = serializers.SerializerMethodField()

    class Meta:
        fields = ('id',
                  'title',
                  'author',
                  'doer',
                  'applicants',
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

    def get_applicants(self, task):
        applicantions = task.applications.all()
        applicants = [application.applicant.username for application in applicantions]
        return applicants


class TaskDetailSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    doer = serializers.CharField(source='doer.username', read_only=True)
    applicants = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    expires_at = serializers.CharField(read_only=True)

    class Meta:
        fields = ('id',
                  'author',
                  'doer',
                  'applicants',
                  'title',
                  'difficulty_stage_of_study',
                  'difficulty_course_of_study',
                  'tags',
                  'subject',
                  'description',
                  'stop_accepting_applications_at',
                  'status',
                  'created_at',
                  'updated_at',
                  'expires_at',
                  )
        model = Task

    def get_applicants(self, task):
        applicantions = task.applications.all()
        applicants = [application.applicant.username for application in applicantions]
        return applicants


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


# функции от модели такс, которые нужно вынести сюда
def add_file(self, file):
    # TODO
    pass


def delete_file(self):
    # TODO
    pass


def set_doer(self):
    # TODO
    pass


def check_if_expired(self):
    # TODO
    pass
