from rest_framework.decorators import action
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class MachineUsersRelaxedViewSet(MachineAuthViewSet):
    """Viewset with a custom action not declared in the test module registry."""

    module = "users"

    def list(self, request):
        return Response({"ok": True, "action": "list"})

    @action(detail=False, methods=["get"])
    def export(self, request):
        return Response({"ok": True, "action": "export"})
