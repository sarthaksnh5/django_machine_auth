from django.core.exceptions import ImproperlyConfigured
from django.urls import get_resolver

from django_machine_auth.exceptions import MachineAuthConfigurationError
from django_machine_auth.registry.module_registry import get_module


def _walk_patterns(urlpatterns):
    for pattern in urlpatterns:
        if hasattr(pattern, "url_patterns"):
            yield from _walk_patterns(pattern.url_patterns)
            continue
        yield pattern


def validate_machine_viewsets():
    try:
        from django_machine_auth.views.base_viewset import MachineAuthViewSet
        patterns = get_resolver().url_patterns
    except (ImportError, ImproperlyConfigured):
        return

    for pattern in _walk_patterns(patterns):
        callback = getattr(pattern, "callback", None)
        view_cls = getattr(callback, "cls", None)
        if not view_cls:
            continue
        if not issubclass(view_cls, MachineAuthViewSet):
            continue

        module_name = getattr(view_cls, "module", None)
        if not module_name:
            raise MachineAuthConfigurationError(f"{view_cls.__name__} must define module")
        if get_module(module_name) is None:
            raise MachineAuthConfigurationError(
                f"Module '{module_name}' used by {view_cls.__name__} is not registered"
            )
        _validate_custom_actions(view_cls, module_name)


def _validate_custom_actions(view_cls, module_name):
    module_data = get_module(module_name) or {}
    declared_actions = module_data.get("actions", {})
    for action in view_cls.get_extra_actions():
        action_name = action.__name__
        if action_name not in declared_actions:
            raise MachineAuthConfigurationError(
                f'Action "{action_name}" found in {view_cls.__name__} but not defined in module '
                f'"{module_name}". Add it to your <app>/api_key_perm.py module actions mapping.'
            )
        defined_methods = set(declared_actions.get(action_name, []))
        used_methods = set(getattr(action, "mapping", {}).keys())
        missing_methods = sorted(used_methods - defined_methods)
        if missing_methods:
            raise MachineAuthConfigurationError(
                f'Action "{action_name}" in {view_cls.__name__} uses methods {missing_methods} '
                f'not declared in module "{module_name}". Add them to <app>/api_key_perm.py.'
            )
