from django_machine_auth.utils.permission_resolver import resolve_permission


def test_resolve_crud_permission():
    assert resolve_permission("users", "list", "GET") == "users.view"


def test_resolve_action_permission():
    assert resolve_permission("users", "reset_password", "POST") == "users.reset_password.post"
