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
