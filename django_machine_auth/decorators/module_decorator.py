from django_machine_auth.registry.module_registry import register_module


def api_key_module(module_name, label=None):
    def decorator(cls):
        crud = getattr(cls, "crud", ["view", "create", "update", "delete"])
        actions = getattr(cls, "actions", {})
        register_module(module_name, label or module_name.title(), crud=crud, actions=actions)
        return cls

    return decorator
