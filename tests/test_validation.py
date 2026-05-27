import pytest
from django.test import override_settings

from django_machine_auth.exceptions import MachineAuthConfigurationError
from django_machine_auth.registry.module_registry import MODULE_REGISTRY, register_module
from django_machine_auth.views.validation import _validate_custom_actions


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


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": True})
def test_validate_custom_actions_raises_when_action_missing_from_module():
    MODULE_REGISTRY.clear()
    register_module("users", "Users", actions={"profile": ["get"]})
    view_cls = _build_viewset([_build_action("reset_password", ["post"])])

    with pytest.raises(MachineAuthConfigurationError) as exc:
        _validate_custom_actions(view_cls, "users")
    assert "api_key_perm.py" in str(exc.value)


@override_settings(MACHINE_AUTH={"STRICT_ACTION_VALIDATION": True})
def test_validate_custom_actions_raises_when_method_missing_from_module():
    MODULE_REGISTRY.clear()
    register_module("users", "Users", actions={"profile": ["get"]})
    view_cls = _build_viewset([_build_action("profile", ["get", "post"])])

    with pytest.raises(MachineAuthConfigurationError) as exc:
        _validate_custom_actions(view_cls, "users")
    assert "methods ['post']" in str(exc.value)
