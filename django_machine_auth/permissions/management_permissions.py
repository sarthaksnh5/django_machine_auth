from rest_framework.permissions import BasePermission


class CanManageMachineAPIKeys(BasePermission):
    """Superusers manage all keys; authenticated users manage only their own keys."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user_id == request.user.id
