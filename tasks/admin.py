from django.contrib import admin
from .models import Task, TaskTag, TaskSubject


class TaskAdmin(admin.ModelAdmin):
    model = Task
    list_display = ('task_id', 'author', 'doer', 'title',
                    'difficulty_stage_of_study', 'difficulty_course_of_study',
                    'get_tags', 'subject', 'description', 'status', 'created_at', 'updated_at', 'expires_at')

    fieldsets = (
        ('Task short info', {'fields': ('title', )}),
        ('Author and Doer', {'fields': ('author', 'doer')}),
        ('Task info', {'fields': ('description', 'subject', 'tags', 'status')}),
        ('Difficulty', {'fields': ('difficulty_stage_of_study', 'difficulty_course_of_study')}),
        ("Deadline", {"fields": ('expires_at',)})
    )


class TaskTagAdmin(admin.ModelAdmin):
    model = TaskTag
    list_display = ('tag_name', )


class TaskSubjectAdmin(admin.ModelAdmin):
    model = TaskSubject
    list_display = ('subject_name', )


# Register your models here.
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskTag, TaskTagAdmin)
admin.site.register(TaskSubject, TaskSubjectAdmin)
