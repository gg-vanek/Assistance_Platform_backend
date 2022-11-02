from rest_framework import permissions


class IsTaskOwnerOrReadOnly(permissions.BasePermission):
    # Also if user is_staff it means that he "is account owner"
    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS or request.user.is_superuser or request.user.is_staff:
            # SAFE_METHODS are available for everyone
            # superuser can do whatever he wants hehe
            return True
        return False
