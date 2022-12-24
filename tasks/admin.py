from django.contrib import admin
from .models import Task, TaskTag, TaskSubject, TaskFile, Application


class TaskAdmin(admin.ModelAdmin):
    model = Task
    list_display = ('task_id', 'author', 'doer', 'list_applicants', 'title',
                    'difficulty_stage_of_study', 'difficulty_course_of_study',
                    'list_tags', 'subject', 'description', 'status',
                    'created_at', 'stop_accepting_applications_at', 'expires_at')

    fieldsets = (
        ('Task short info', {'fields': ('title',)}),
        ('Author and Doer', {'fields': ('author', 'doer')}),
        ('Task info', {'fields': ('description', 'subject', 'tags', 'status')}),
        ('Difficulty', {'fields': ('difficulty_stage_of_study', 'difficulty_course_of_study')}),
        ("Deadlines", {"fields": ('stop_accepting_applications_at', 'expires_at',)}),
        ("Files", {"fields": ('files',)})
    )


class TaskTagAdmin(admin.ModelAdmin):
    model = TaskTag
    list_display = ('tag_name', 'id')


class TaskSubjectAdmin(admin.ModelAdmin):
    model = TaskSubject
    list_display = ('subject_name',)


class TaskFileAdmin(admin.ModelAdmin):
    model = TaskFile
    list_display = ('filename', 'file')

    # fields = [field.name for field in model._meta.fields if field.name != "id"]
    exclude = ('id',)


class ApplicationAdmin(admin.ModelAdmin):
    model = Application
    list_display = ('applicant', 'message', 'created_at', 'updated_at')

    # fields = [field.name for field in model._meta.fields if field.name != "id"]
    exclude = ('id',)


# Register your models here.
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskTag, TaskTagAdmin)
admin.site.register(TaskSubject, TaskSubjectAdmin)
admin.site.register(TaskFile, TaskFileAdmin)
admin.site.register(Application, ApplicationAdmin)
