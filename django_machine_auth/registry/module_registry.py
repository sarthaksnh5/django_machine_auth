from __future__ import annotations

from copy import deepcopy
from importlib import import_module

from django.apps import apps

MODULE_REGISTRY = {}
CRUD_PERMISSIONS = {"view", "create", "update", "delete"}


def _normalize_methods(methods):
    return [str(method).lower() for method in methods]


def _build_permissions(module_name, crud, actions):
    permissions = []
    for perm in crud:
        permissions.append(f"{module_name}.{perm}")
    for action_name, methods in actions.items():
        for method in _normalize_methods(methods):
            permissions.append(f"{module_name}.{action_name}.{method}")
    return sorted(set(permissions))


def _label_for_permission(permission):
    tail = permission.split(".", 1)[-1].replace(".", " ").replace("_", " ")
    return tail.title()


def register_module(module_name, label, crud=None, actions=None):
    crud = [p.lower() for p in (crud or ["view", "create", "update", "delete"])]
    actions = actions or {}
    invalid = set(crud) - CRUD_PERMISSIONS
    if invalid:
        raise ValueError(f"Invalid CRUD permissions for module '{module_name}': {sorted(invalid)}")

    MODULE_REGISTRY[module_name] = {
        "label": label,
        "crud": crud,
        "actions": {k: _normalize_methods(v) for k, v in actions.items()},
        "permissions": _build_permissions(module_name, crud, actions),
    }


def get_registry():
    return deepcopy(MODULE_REGISTRY)


def get_module(module_name):
    return MODULE_REGISTRY.get(module_name)


def iter_permission_rows():
    for module_name, data in MODULE_REGISTRY.items():
        for permission in data["permissions"]:
            yield {
                "module": module_name,
                "permission": permission,
                "label": _label_for_permission(permission),
            }


def discover_modules():
    for app_config in apps.get_app_configs():
        module_path = f"{app_config.name}.api_key_perm"
        try:
            import_module(module_path)
        except ModuleNotFoundError as exc:
            if exc.name != module_path:
                raise
            continue
