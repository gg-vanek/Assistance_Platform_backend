from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'age', 'stage_of_study', 'years_of_study')

    fieldsets = (
        ('Account info', {'fields': ('username', 'email')}),
        ('Person\'s info', {'fields': ('first_name', 'last_name', 'age')}),
        ('Education', {'fields': ('stage_of_study', 'years_of_study')}),

        ("Permissions", {"fields": (
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions")
        }),

        ("Important dates", {"fields": ("last_login", "date_joined")})
    )


admin.site.register(CustomUser, CustomUserAdmin)
