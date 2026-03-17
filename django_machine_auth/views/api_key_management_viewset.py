from rest_framework import mixins, permissions
from rest_framework.viewsets import GenericViewSet

from django_machine_auth.serializers import MachineAPIKeyCreateSerializer


class MachineAPIKeyManagementViewSet(mixins.CreateModelMixin, GenericViewSet):
    """
    Admin-only endpoint for issuing machine API keys.

    Required payload fields:
    - name
    - user
    - permissions
    Optional:
    - expires_at
    """

    serializer_class = MachineAPIKeyCreateSerializer
    permission_classes = [permissions.IsAdminUser]
