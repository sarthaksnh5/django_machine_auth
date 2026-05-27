import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APIRequestFactory

from django_machine_auth.permissions import MachineAuthPermission
from django_machine_auth.registry.module_registry import MODULE_REGISTRY, register_module
from django_machine_auth.utils.hashing import hash_api_key
from django_machine_auth.utils.permission_resolver import should_enforce_permission
from django_machine_auth.views.validation import _validate_custom_actions


pytestmark = pytest.mark.django_db


def _build_action(name, methods):
    def _fn():
        return None

    _fn.__name__ = name
    _fn.mapping = {method: name for method in methods}
    return _fn


def _build_viewset(action_defs):
    class DummyViewSet:
        __name__ = "DummyViewSet"

        @staticmethod
        def get_extra_actions():
            return action_defs

    return DummyViewSet


def _seed_registry():
    MODULE_REGISTRY.clear()
    register_module(
        "users",
        "User Management",
        crud=["view", "create", "update", "delete"],
        actions={"profile": ["get", "post"]},
    )


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": True})
def test_should_enforce_permission_always_true_when_strict():
    _seed_registry()
    assert should_enforce_permission("users", "export", "GET") is True


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": False})
def test_should_enforce_permission_false_for_undeclared_custom_action():
    _seed_registry()
    assert should_enforce_permission("users", "export", "GET") is False
    assert should_enforce_permission("users", "list", "GET") is True
    assert should_enforce_permission("users", "profile", "GET") is True


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": True})
def test_validate_custom_actions_raises_when_strict():
    MODULE_REGISTRY.clear()
    register_module("users", "Users", actions={"profile": ["get"]})
    view_cls = _build_viewset([_build_action("reset_password", ["post"])])

    from django_machine_auth.exceptions import MachineAuthConfigurationError

    with pytest.raises(MachineAuthConfigurationError):
        _validate_custom_actions(view_cls, "users")


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": False})
def test_validate_custom_actions_warns_when_relaxed(caplog):
    import logging

    MODULE_REGISTRY.clear()
    register_module("users", "Users", actions={"profile": ["get"]})
    view_cls = _build_viewset([_build_action("reset_password", ["post"])])

    with caplog.at_level(logging.WARNING):
        _validate_custom_actions(view_cls, "users")

    assert "reset_password" in caplog.text
    assert "api_key_perm.py" in caplog.text


@override_settings(
    ROOT_URLCONF="tests.urls_machine_relaxed",
    MACHINE_AUTH={"KEY_PREFIX": "mac_", "STRICT_ACTION_VALIDATION": False},
)
def test_undeclared_custom_action_allowed_without_permission_when_relaxed():
    _seed_registry()
    from django_machine_auth.models import MachineAPIKey

    user = get_user_model().objects.create_user(username="relaxed-user")
    MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="k",
        user=user,
        hashed_key=hash_api_key("mac_relaxed1"),
        permissions=["users.view"],
    )
    client = APIClient()
    response = client.get(
        "/machine-users-relaxed/export/",
        HTTP_AUTHORIZATION="machine_auth mac_relaxed1",
    )
    assert response.status_code == 200
    assert response.data["action"] == "export"


@override_settings(
    ROOT_URLCONF="tests.urls_machine_relaxed",
    MACHINE_AUTH={"KEY_PREFIX": "mac_", "STRICT_ACTION_VALIDATION": True},
)
def test_undeclared_custom_action_denied_when_strict():
    _seed_registry()
    from django_machine_auth.models import MachineAPIKey

    user = get_user_model().objects.create_user(username="strict-user")
    MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="k",
        user=user,
        hashed_key=hash_api_key("mac_strict1"),
        permissions=["users.view"],
    )
    client = APIClient()
    response = client.get(
        "/machine-users-relaxed/export/",
        HTTP_AUTHORIZATION="machine_auth mac_strict1",
    )
    assert response.status_code == 403


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": False})
def test_declared_custom_action_still_requires_permission_when_relaxed():
    _seed_registry()
    factory = APIRequestFactory()
    request = factory.get("/")
    request.machine_api_key = type(
        "Key",
        (),
        {"permissions": ["users.view"]},
    )()

    class View:
        module = "users"
        action = "profile"

    permission = MachineAuthPermission()
    assert permission.has_permission(request, View()) is False

    request.machine_api_key.permissions = ["users.profile.get"]
    assert permission.has_permission(request, View()) is True
