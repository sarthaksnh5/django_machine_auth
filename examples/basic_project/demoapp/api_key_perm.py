from django_machine_auth.decorators import api_key_module


@api_key_module("users", label="User Management")
class UsersModule:
    crud = ["view", "create", "update", "delete"]
    actions = {"profile": ["get"]}
