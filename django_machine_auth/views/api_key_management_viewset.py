from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from django_machine_auth.models import MachineAPIKey
from django_machine_auth.permissions.management_permissions import CanManageMachineAPIKeys
from django_machine_auth.serializers import (
    MachineAPIKeyCreateSerializer,
    MachineAPIKeyDetailSerializer,
    MachineAPIKeyListSerializer,
    MachineAPIKeyUpdateSerializer,
)


class MachineAPIKeyManagementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """
    Manage machine API keys.

    - Superuser: full access to all keys; can create for any user.
    - Authenticated user: own keys only; can create for self.
  """

    permission_classes = [CanManageMachineAPIKeys]

    def get_queryset(self):
        queryset = MachineAPIKey.objects.select_related("user").order_by("-created_at")  # pylint: disable=no-member
        if self.request.user.is_superuser:
            user_id = self.request.query_params.get("user")
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return MachineAPIKeyCreateSerializer
        if self.action in {"update", "partial_update"}:
            return MachineAPIKeyUpdateSerializer
        if self.action == "retrieve":
            return MachineAPIKeyDetailSerializer
        return MachineAPIKeyListSerializer

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(MachineAPIKeyDetailSerializer(obj).data, status=status.HTTP_200_OK)
