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
        ('Contact info', {'fields': ('phone', 'telegram', 'vk')}),
        ("Permissions", {"fields": (
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions")
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")},),
        ("Ratings", {"fields": ("author_rating", "author_review_counter", "author_rating_normalized",
                                "implementer_rating", "implementer_review_counter", "implementer_rating_normalized",)},)
    )


admin.site.register(User, CustomUserAdmin)
