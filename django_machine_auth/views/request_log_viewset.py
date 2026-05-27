from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_machine_auth.models import APIKeyRequestLog, MachineAPIKey
from django_machine_auth.permissions.log_permissions import CanViewMachineAPIKeyLogs
from django_machine_auth.serializers import (
    MachineAPIKeyRequestLogDetailSerializer,
    MachineAPIKeyRequestLogListSerializer,
)


class MachineAPIKeyRequestLogViewSet(ReadOnlyModelViewSet):
    """
    Read-only access to machine-auth request logs.

    - Superuser: all logs; optional ?user= and ?api_key= filters.
    - Authenticated user: logs for API keys they own; ?api_key= must be their key (else 403).

    Requires ENABLE_REQUEST_LOGGING and MachineAuthLoggingMiddleware for new log rows.
    """

    permission_classes = [CanViewMachineAPIKeyLogs]

    def get_queryset(self):
        queryset = APIKeyRequestLog.objects.select_related("api_key", "user").order_by("-created_at")  # pylint: disable=no-member

        if self.request.user.is_superuser:
            user_id = self.request.query_params.get("user")
            if user_id:
                queryset = queryset.filter(Q(user_id=user_id) | Q(api_key__user_id=user_id))
            api_key_id = self.request.query_params.get("api_key")
            if api_key_id:
                queryset = queryset.filter(api_key_id=api_key_id)
            return queryset

        queryset = queryset.filter(api_key__user=self.request.user)
        api_key_id = self.request.query_params.get("api_key")
        if api_key_id:
            if not MachineAPIKey.objects.filter(pk=api_key_id, user=self.request.user).exists():  # pylint: disable=no-member
                raise PermissionDenied("You do not have access to this API key's logs.")
            queryset = queryset.filter(api_key_id=api_key_id)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MachineAPIKeyRequestLogDetailSerializer
        return MachineAPIKeyRequestLogListSerializer
