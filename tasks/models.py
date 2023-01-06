import datetime

from django.db import models
from users.models import User, STAGE_OF_STUDY_CHOICES
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator

TASK_STATUS_CHOICES = [('A', 'accepting applications'), ('P', 'in progress'), ('C', 'closed')]


class TaskTag(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    def __str__(self):
        return self.name


class TaskSubject(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='author')
    doer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doer')
    title = models.CharField(max_length=255)
    price = models.IntegerField(default=None, null=True)

    difficulty_stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    difficulty_course_of_study = models.IntegerField(default=0, validators=[
        MinValueValidator(0),
        MaxValueValidator(15),
    ])
    tags = models.ManyToManyField(TaskTag)
    subject = models.ForeignKey(TaskSubject, on_delete=models.SET_NULL, null=True)
    description = models.TextField()

    status = models.CharField(max_length=1, choices=TASK_STATUS_CHOICES)

    # dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stop_accepting_applications_at = models.DateTimeField()
    expires_at = models.DateTimeField(default=None, null=True)
    closed_at = models.DateTimeField(default=None, null=True)
    # этот список нужен, чтобы фронт знал по каким датам можно производить фильтрацию
    datetime_fileds_names = {'created_at': 'Дата создания',
                             'updated_at': 'Дата последнего редактирования',
                             'stop_accepting_applications_at': 'Дата окончания приема заявок',
                             'expires_at': 'Дедлайн по задаче',
                             'closed_at': 'Дата закрытия задачи'}  # последнее поле - задача уже выполнена

    author_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], blank=True, null=True)
    review_on_author = models.TextField(blank=True)
    doer_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], blank=True, null=True)
    review_on_doer = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def admin_list_applicants(self):
        # только для использоавния в админке
        return ", ".join([application.applicant.username for application in self.applications.all()])

    def admin_list_tags(self):
        # только для использоавния в админке
        return ", ".join([tag.name for tag in self.tags.all()])


class Application(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    message = models.CharField(max_length=500, blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='applications')
    status = models.CharField(default='S', max_length=1, choices=[('A', 'accepted'), ('R', 'rejected'), ('S', 'sent')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['applicant', 'task']

    def __str__(self):
        return str(self.applicant) + '. task ' + str(self.task.id) + '. application ' + str(self.id)


class TaskFile(models.Model):
    filename = models.CharField(max_length=50, blank=False)
    file = models.FileField(upload_to=os.path.join(settings.MEDIA_ROOT, f'tasks/task_files'))
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')

    def __str__(self):
        return self.filename
