from rest_framework.decorators import action
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class DemoUserViewSet(MachineAuthViewSet):
    module = "users"

    def list(self, request):
        return Response({"result": "ok", "action": "list"})

    @action(detail=False, methods=["get"])
    def profile(self, request):
        return Response({"result": "ok", "action": "profile"})
