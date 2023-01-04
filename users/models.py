from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator

STAGE_OF_STUDY_CHOICES = [
    ('N', 'None'),
    ('S', 'School'),
    ('C', 'College'),
    ('B', "bachelor's degree"),
    ('M', "master's degree"),
    ('PG', "postgraduate study"),
]


class User(AbstractUser):
    # TODO добавить уникальность эмейла при сохранении
    # добавить проверку на неравенство username 'my_profile', 'registration'
    biography = models.TextField(blank=True)

    profile_image = models.ImageField(null=True, blank=True,
                                      upload_to=os.path.join(settings.MEDIA_ROOT,
                                                             f'users/user_profile_images'))

    stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    course_of_study = models.IntegerField(default=1, validators=[
        MinValueValidator(1),
        MaxValueValidator(15),
    ])
    contact_phone = models.CharField(max_length=16, blank=True)
    contact_email = models.EmailField(blank=True)

    # TODO добавить больше контактов
    def __str__(self):
        return self.username
