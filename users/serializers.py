from rest_framework import serializers

from tasks.models import Task, Application
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'first_name',
            'last_name',
            'biography',
            'profile_image',
            'stage_of_study',
            'course_of_study',
        )
        model = User


class UserContactSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'first_name',
            'email',
            'phone',
            'telegram',
            'vk',
        )
        model = User


class UserStatisticsSerializer(serializers.ModelSerializer):
    ratings = serializers.SerializerMethodField(read_only=True)
    tasks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('ratings', 'tasks')
        model = User

    def get_ratings(self, user):
        return {'author': {'sum': user.author_rating, 'amount': user.author_review_counter,
                           'normalized': user.author_rating_normalized},
                'implementer': {'sum': user.implementer_rating, 'amount': user.implementer_review_counter,
                                'normalized': user.implementer_rating_normalized}}

    def get_tasks(self, user):
        authored_tasks = Task.objects.filter(author=user)
        implementered_tasks = Task.objects.filter(implementer=user)
        applications = Application.objects.filter(applicant=user)

        return {'authored': {'active': authored_tasks.filter(status__in=['A', 'P']).count(),
                             'total': authored_tasks.count()},
                'implementered': {'active': implementered_tasks.filter(status='P').count(),
                                  'total': implementered_tasks.count()},
                'applications': {'active': applications.filter(status='S').count(),
                                 'total': applications.count()}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'email',)
        model = User


class UserDetailSerializer(serializers.ModelSerializer):
    statistics = serializers.SerializerMethodField(read_only=True)
    contact = serializers.SerializerMethodField(read_only=True)
    profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('id',
                  'username',
                  'email',
                  'profile',
                  'contact',
                  'statistics')
        model = User

    def get_statistics(self, user):
        return UserStatisticsSerializer(user).data

    def get_contact(self, user):
        if self.context['request'].user == user:
            # контакты возвращаются только если юзер пытается просмотреть сам себя
            return UserContactSerializer(user).data
        else:
            return None

    def get_profile(self, user):
        return UserProfileSerializer(user).data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, max_length=128, write_only=True)

    class Meta:
        fields = ('username',
                  'password',
                  'email',)
        model = User

    def create(self, validated_data):
        # TODO добавить подтверждение по email
        return User.objects.create_user(**validated_data)
