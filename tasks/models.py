from django.db import models

from notifications.models import new_notification
from users.models import User, STAGE_OF_STUDY_CHOICES
from django.conf import settings
import os
from django.core.validators import MaxValueValidator, MinValueValidator

TASK_STATUS_CHOICES = [('A', 'accepting applications'), ('P', 'in progress'), ('C', 'closed')]


class TaskTag(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskSubject(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='author')
    implementer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='implementer')
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

    def __str__(self):
        return str(self.id)

    def admin_list_applicants(self):
        # только для использоавния в админке
        return ", ".join([application.applicant.username for application in self.applications.all()])

    def admin_list_tags(self):
        # только для использоавния в админке
        return ", ".join([tag.name for tag in self.tags.all()])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TODO переделать если добавится модерация
        # уведомление автору задачи
        new_notification(user=self.author,
                         type='created_task',
                         affected_object_id=self.id,
                         message=f"Ваше задание {self.id} успешно создано/отредактировано/закрыто",
                         checked=0)


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # notification_to_applicant
        new_notification(user=self.applicant,
                         type='created_application',
                         affected_object_id=self.task.id,
                         message=f"Ваша заявка на задание {self.task.id} "
                                 f"успешно создана/отредактирована",
                         checked=0)
        # notification_to_author
        new_notification(send_email=True,
                         user=self.task.author,
                         type='received_application',
                         affected_object_id=self.task.id,
                         message=f"На ваше задание {self.task.id} подали заявку",
                         checked=0)


class TaskFile(models.Model):
    filename = models.CharField(max_length=50, blank=False)
    file = models.FileField(upload_to=os.path.join(settings.MEDIA_ROOT, f'tasks/task_files'))
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')

    def __str__(self):
        return self.filename


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reviews')

    review_type = models.CharField(max_length=1, choices=[('A', 'as author'), ('I', 'as implementer')])

    message = models.TextField(blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('reviewer', 'task')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.task.author == self.reviewer:
            receiver = self.task.implementer
        elif self.task.implementer == self.reviewer:
            receiver = self.task.author

        # notification_to_reviewer
        new_notification(user=self.reviewer,
                         type='created_review',
                         affected_object_id=self.task.id,
                         message=f"Вы успешно создали/отредактировали отзыв к заданию {self.task.id}",
                         checked=0)
        # notification_to_receiver
        new_notification(user=receiver,
                         type='received_review',
                         affected_object_id=self.task.id,
                         message=f"Был создан/изменен отзыв о вас по заданию {self.task.id}",
                         checked=0)
