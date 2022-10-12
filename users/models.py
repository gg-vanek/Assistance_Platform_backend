from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os


class CustomUser(AbstractUser):
    # username = models.CharField(max_length=50, unique=True)
    # first_name = models.CharField(max_length=30)
    # last_name = models.CharField(max_length=30, blank=True)
    age = models.IntegerField(default=0)
    biography = models.TextField(blank=True)

    STAGE_OF_STUDY_CHOICES = [
        ('N', 'None'),
        ('S', 'School'),
        ('C', 'College'),
        ('B', "bachelor's degree"),
        ('M', "master's degree"),
        ('PG', "postgraduate study"),
    ]

    # текущая ступень обучения
    stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    # сколько полных лет на текущей ступени обучения от 0 до ...
    # переименовать на course или типа того
    course_of_study = models.IntegerField(default=0)
    profile_image = models.ImageField(null=True, blank=True, upload_to=os.path.join(settings.BASE_DIR,
                                                                                    'data/user_profile_images'))

    def __str__(self):
        return self.username

# ('username', 'email', 'first_name', 'last_name', 'age', 'stage_of_study', 'course_of_study', 'profile_image')
