from rest_framework.permissions import BasePermission

from django_machine_auth.registry.module_registry import get_module
from django_machine_auth.utils.permission_resolver import resolve_permission


class MachineAuthPermission(BasePermission):
    message = "Machine key does not have required permission"

    def has_permission(self, request, view):
        api_key = getattr(request, "machine_api_key", None)
        if not api_key:
            return False

        module_name = getattr(view, "module", None)
        if not module_name:
            return False
        if get_module(module_name) is None:
            return False

        action = getattr(view, "action", "")
        required = resolve_permission(module_name, action, request.method)
        return required in set(getattr(api_key, "permissions", []) or [])
