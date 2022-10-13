from django.db import models
from users.models import CustomUser
from django.conf import settings
import os


class TaskTag(models.Model):
    tag_name = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.tag_name


class TaskSubject(models.Model):
    subject_name = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.subject_name


class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='author')
    doer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='doer')
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
    difficulty_course_of_study = models.IntegerField(default=0)
    tags = models.ManyToManyField(TaskTag)
    subject = models.ForeignKey(TaskSubject, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    ####
    # extra_files = models.FilePathField(path=os.path.join(settings.BASE_DIR, f'/tasks_data/{task_id}'), blank=True)
    ####
    STATUS_CHOICES = [('A', 'accepting applications'), ('P', 'in progress'), ('C', 'completed')]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    RATING_CHOICES = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]
    time_rate = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    accuracy_rate = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    created_at = models.TimeField(auto_now_add=True)
    updated_at = models.TimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=False)

    def __str__(self):
        return self.title

    def get_tags(self):
        return ", ".join([tag.tag_name for tag in self.tags.all()])

