from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'stage_of_study', 'course_of_study')

    fieldsets = (
        ('Account info', {'fields': ('username', 'email', 'password')}),
        ('Person\'s info', {'fields': ('first_name', 'last_name')}),
        ('Education', {'fields': ('stage_of_study', 'course_of_study')}),
        ('Profile info', {'fields': ('profile_image', 'biography')}),
        ('Contact info', {'fields': ('contact_phone', 'contact_email', 'contact_tg', 'contact_vk')}),
        ("Permissions", {"fields": (
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions")
        }),

        ("Important dates", {"fields": ("last_login", "date_joined")})
    )


admin.site.register(User, CustomUserAdmin)
