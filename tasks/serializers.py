from rest_framework import serializers

from users.models import User
from users.serializers import UserContactSerializer
from .models import Task, Application, TaskTag, TaskSubject


# informational serializers
class TagInfoSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name',)
        model = TaskTag


class SubjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name',)
        model = TaskSubject


# display/edit serializers
class TaskSerializer(serializers.ModelSerializer):
    applicants = serializers.SerializerMethodField(read_only=True)

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
        applications = task.applications.all()
        applicants = [application.applicant.username for application in applications]
        return applicants


class TaskDetailSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    doer = serializers.CharField(source='doer.username', read_only=True)
    applicants = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    expires_at = serializers.CharField(read_only=True)

    author_contacts = serializers.SerializerMethodField(read_only=True)
    doer_contacts = serializers.SerializerMethodField(read_only=True)

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
                  'author_contacts',
                  'doer_contacts',)
        model = Task

    def get_applicants(self, task):
        applications = task.applications.all()
        applicants = [application.applicant.username for application in applications]
        return applicants

    def get_author_contacts(self, task):
        user = self.context['request'].user
        if user == task.doer:
            return UserContactSerializer(task.author).data
        else:
            return None

    def get_doer_contacts(self, task):
        user = self.context['request'].user
        if user == task.author:
            return UserContactSerializer(task.doer).data
        else:
            return None


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('id',
                  'applicant',
                  'applicant_username',
                  'message',
                  'task',
                  'status',
                  'created_at',
                  'updated_at',)
        model = Application

    def get_applicant_username(self, application):
        return application.applicant.username


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant = serializers.CharField(source='applicant.username', read_only=True)
    task = serializers.CharField(source='task.id', read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

    class Meta:
        fields = ('id', 'applicant', 'task', 'status', 'message', 'created_at', 'updated_at',)
        model = Application


# task interact serializers
class TaskApplySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('message',)
        model = Application


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


class SetTaskDoerSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    applications = serializers.SerializerMethodField(read_only=True)
    doer = serializers.SerializerMethodField(method_name='set_doer')
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        fields = ('id',
                  'author',
                  'doer',
                  'applications',
                  'title',
                  'status',)
        model = Task

    def set_doer(self, task):
        doer_id = self.context['request'].data.get('doer')
        if doer_id is None or self.context['request'].method != 'PUT':
            if task.doer is not None:
                return task.doer.id
            return task.doer

        # если еще нет doer; если accepting applications
        assert (task.doer is None), f'This task (id = {task.id}) already have doer'
        assert (task.status == 'A'), f'This task (id = {task.id}) status is {task.status}. ' \
                                     f'It is not Acception Applications'
        assert (doer_id in [application.applicant.id for application in task.applications.all()]), \
            f'This user (id={doer_id}) haven\'t send application for this task (id={task.id})'

        # если юзер у задания еще не задан,
        # если задание принимает заявки,
        # если юзер подавал заявку на исполнение, то
        # иными словами "если все норм"
        task.status = 'P'  # задание переходит в режим IN PROGRESS
        task.doer = User.objects.get(id=doer_id)  # задать юзера как исполнителя
        task.save()

        applications = task.applications.all()
        for application in applications:
            if application.applicant.id == doer_id:
                application.status = 'A'  # статус ACCEPTED
            else:
                application.status = 'R'  # статус REJECTED
            application.save()

        # TODO TODO TODO обмен контактами

        return doer_id

    def get_applications(self, task):
        applications = task.applications.all()
        applications_info = [ApplicationSerializer(application).data for application in applications]
        return applications_info


class ReviewOnTaskDetailSerializer(serializers.ModelSerializer):
    # выдает всю инфу о задании в рид онли.
    # принимает 2 поля рейтинг и отзыв, но они доступны только для создателя задачи и исполнителя.
    # в зависимости от того, кто сделал запрос заносить ре
    class Meta:
        fields = ('id',
                  'title',
                  'doer',
                  'status',
                  'closed')
        model = Task

