from rest_framework.decorators import action
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class MachineUsersViewSet(MachineAuthViewSet):
    module = "users"

    def list(self, request):
        return Response({"ok": True, "action": "list"})

    def create(self, request):
        return Response({"ok": True, "action": "create"}, status=201)

    @action(detail=False, methods=["get", "post"])
    def profile(self, request):
        return Response({"ok": True, "action": "profile", "method": request.method})
