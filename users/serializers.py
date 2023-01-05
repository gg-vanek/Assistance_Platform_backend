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

    author_rating_sum = serializers.IntegerField(read_only=True)
    author_rating_count = serializers.IntegerField(read_only=True)
    doer_rating_sum = serializers.IntegerField(read_only=True)
    doer_rating_count = serializers.IntegerField(read_only=True)

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
                  'doer_rating_count',)
        model = User


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
