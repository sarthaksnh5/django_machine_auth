from rest_framework.viewsets import GenericViewSet

from django_machine_auth.authentication import MachineAPIKeyAuthentication
from django_machine_auth.permissions import MachineAuthPermission
from django_machine_auth.throttling import MachineAPIKeyRateThrottle


class MachineAuthViewSet(GenericViewSet):
    authentication_classes = [MachineAPIKeyAuthentication]
    permission_classes = [MachineAuthPermission]
    throttle_classes = [MachineAPIKeyRateThrottle]
    module = None

    def initial(self, request, *args, **kwargs):
        if not self.module:
            raise AssertionError("MachineAuthViewSet requires `module`")
        return super().initial(request, *args, **kwargs)
