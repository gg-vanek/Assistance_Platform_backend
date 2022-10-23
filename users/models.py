from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator


class CustomUser(AbstractUser):
    user_id = models.IntegerField(primary_key=True, auto_created=True)

    # username = models.CharField(max_length=50, unique=True)
    # first_name = models.CharField(max_length=30)
    # last_name = models.CharField(max_length=30, blank=True)
    age = models.IntegerField(default=0, validators=[
        MinValueValidator(1),
        MaxValueValidator(150),
    ])
    biography = models.TextField(blank=True)

    STAGE_OF_STUDY_CHOICES = [
        ('N', 'None'),
        ('S', 'School'),
        ('C', 'College'),
        ('B', "bachelor's degree"),
        ('M', "master's degree"),
        ('PG', "postgraduate study"),
    ]
    profile_image = models.ImageField(null=True, blank=True,
                                      upload_to=os.path.join(settings.MEDIA_ROOT,
                                                             f'users/user_profile_images'))
    # текущая ступень обучения
    stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    # сколько полных лет на текущей ступени обучения от 0 до ...
    # переименовать на course или типа того
    course_of_study = models.IntegerField(default=0, validators=[
        MinValueValidator(1),
        MaxValueValidator(20),
    ])
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.username
