from rest_framework.permissions import BasePermission


class CanViewMachineAPIKeyLogs(BasePermission):
    """Superusers view all logs; authenticated users view logs for API keys they own."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.api_key_id is not None and obj.api_key.user_id == request.user.id
