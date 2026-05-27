from django_machine_auth.registry.module_registry import get_module
from django_machine_auth.utils.settings import strict_action_validation

CRUD_ACTION_MAP = {
    "list": "view",
    "retrieve": "view",
    "create": "create",
    "update": "update",
    "partial_update": "update",
    "destroy": "delete",
}


def resolve_permission(module: str, action: str, method: str) -> str:
    if action in CRUD_ACTION_MAP:
        return f"{module}.{CRUD_ACTION_MAP[action]}"
    return f"{module}.{action}.{method.lower()}"


def should_enforce_permission(module_name: str, action: str, method: str) -> bool:
    """Return False for undeclared custom actions when strict validation is disabled."""
    if action in CRUD_ACTION_MAP:
        return True
    if strict_action_validation():
        return True
    module_data = get_module(module_name) or {}
    declared_actions = module_data.get("actions") or {}
    return action in declared_actions
