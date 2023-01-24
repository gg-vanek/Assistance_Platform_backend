from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.functional import lazy
from django.utils.translation import gettext

STAGE_OF_STUDY_CHOICES = [
    ('N', 'None'),
    ('S', 'School'),
    ('C', 'College'),
    ('B', "bachelor's degree"),
    ('M', "master's degree"),
    ('PG', "postgraduate study"),
]

gettext_lazy = lazy(gettext, str)

RESERVED_SYSTEM_WORDS = ['my_profile', 'registration', 'id']


def not_reserved_system_word_validator(username):
    if username in RESERVED_SYSTEM_WORDS:
        raise ValidationError(gettext_lazy('%(username)s is a reserved system word. Choose another username'),
                              params={'value': username}, )


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        gettext_lazy("username"),
        max_length=150,
        unique=True,
        help_text=gettext_lazy(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator, not_reserved_system_word_validator],
        error_messages={
            "unique": gettext_lazy("A user with that username already exists."),
        },
    )
    email = models.EmailField(gettext_lazy("email address"), blank=True, unique=True)

    # информация о профиле пользователя
    biography = models.TextField(null=True, default=None, blank=True)

    profile_image = models.ImageField(null=True, default=None, blank=True,
                                      upload_to=os.path.join(settings.MEDIA_ROOT,
                                                             f'users/user_profile_images'))

    stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    course_of_study = models.IntegerField(default=1, validators=[
        MinValueValidator(1),
        MaxValueValidator(15),
    ])
    # контактная информация
    phone = models.CharField(max_length=30, null=True, default=None, blank=True)
    telegram = models.CharField(max_length=40, null=True, default=None, blank=True)
    vk = models.CharField(max_length=40, null=True, default=None, blank=True)

    # статистическая информация о пользователе
    author_rating = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    author_review_counter = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    author_rating_normalized = models.FloatField(default=7.5, validators=[MinValueValidator(0)])

    implementer_rating = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    implementer_review_counter = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    implementer_rating_normalized = models.FloatField(default=7.5, validators=[MinValueValidator(0)])

    # User settings
    show_contacts = models.BooleanField(default=False)
    send_email_notifications = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def update_author_rating(self):
        if self.author_review_counter == 0:
            pass
        else:
            self.author_rating_normalized = self.author_rating / self.author_review_counter
            self.save()

    def update_implementer_rating(self):
        if self.implementer_review_counter == 0:
            pass
        else:
            self.implementer_rating_normalized = self.implementer_rating / self.implementer_review_counter
            self.save()
