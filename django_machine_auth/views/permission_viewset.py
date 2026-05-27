from rest_framework import permissions
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_machine_auth.models import MachinePermission
from django_machine_auth.serializers import MachinePermissionSerializer


class MachinePermissionViewSet(ReadOnlyModelViewSet):
    """
    Read-only catalog of assignable permissions (DB-backed).

    Built-in filters:
    - ?module=complaint
    - ?search=profile

    Override get_queryset() in a subclass to restrict visible permissions per role/app.
    """

    serializer_class = MachinePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MachinePermission.objects.all().order_by("module", "permission")  # pylint: disable=no-member
        module = self.request.query_params.get("module")
        search = self.request.query_params.get("search")

        if module:
            queryset = queryset.filter(module=module)
        if search:
            queryset = queryset.filter(permission__icontains=search) | queryset.filter(
                label__icontains=search
            )
        return queryset
