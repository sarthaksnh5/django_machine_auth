from django_machine_auth.registry.module_registry import MODULE_REGISTRY, register_module


def test_register_module_generates_permissions():
    MODULE_REGISTRY.clear()
    register_module(
        "users",
        "User Management",
        crud=["view", "create", "update", "delete"],
        actions={"profile": ["get", "post"]},
    )

    assert "users.view" in MODULE_REGISTRY["users"]["permissions"]
    assert "users.profile.get" in MODULE_REGISTRY["users"]["permissions"]
