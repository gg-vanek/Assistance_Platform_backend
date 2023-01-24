from rest_framework import permissions


class IsAccountOwnerOrReadOnly(permissions.BasePermission):
    # Also if user is_staff it means that he "is account owner"
    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS or request.user.is_superuser:
            # SAFE_METHODS are available for everyone
            # superuser can do whatever he wants hehe
            return True
        if request.user.is_staff and not obj.is_superuser and not obj.is_staff:
            # staff can do whatever they want to any accs except superuser and staff ones
            return True
        return obj == request.user


class IsAccountOwner(permissions.BasePermission):
    # Also if user is_staff it means that he "is account owner"
    def has_object_permission(self, request, view, obj):
        return obj == request.user
