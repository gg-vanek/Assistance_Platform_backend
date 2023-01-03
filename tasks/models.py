import datetime

from django.db import models
from users.models import User
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator


class TaskTag(models.Model):
    name = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.name


class TaskSubject(models.Model):
    name = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.name


class Task(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='author')
    doer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doer')
    title = models.CharField(max_length=255)

    STAGE_OF_STUDY_CHOICES = [
        ('N', 'None'),
        ('S', 'School'),
        ('C', 'College'),
        ('B', "bachelor's degree"),
        ('M', "master's degree"),
        ('PG', "postgraduate study"),
    ]

    difficulty_stage_of_study = models.CharField(max_length=2, choices=STAGE_OF_STUDY_CHOICES, default='N')
    difficulty_course_of_study = models.IntegerField(default=0, validators=[
        MinValueValidator(0),
        MaxValueValidator(15),
    ])
    tags = models.ManyToManyField(TaskTag)
    subject = models.ForeignKey(TaskSubject, on_delete=models.SET_NULL, null=True)
    description = models.TextField()

    STATUS_CHOICES = [('A', 'accepting applications'), ('P', 'in progress'), ('C', 'closed')]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stop_accepting_applications_at = models.DateTimeField()
    expires_at = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(days=7))
    closed_at = models.DateTimeField(default=None, null=True)
    RATING_CHOICES = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]
    time_rate = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    accuracy_rate = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)

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

    def __str__(self):
        return str(self.applicant) + '. task ' + str(self.task.id) + '. application ' + str(self.id)


class TaskFile(models.Model):
    filename = models.CharField(max_length=50, blank=False)
    file = models.FileField(upload_to=os.path.join(settings.MEDIA_ROOT, f'tasks/task_files'))
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')

    def __str__(self):
        return self.filename
