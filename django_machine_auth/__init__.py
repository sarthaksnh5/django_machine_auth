default_app_config = "django_machine_auth.apps.DjangoMachineAuthConfig"

__version__ = "0.3.0"

__all__ = [
    "__version__",
    "api_key_module",
    "MachineAPIKeyAuthentication",
    "MachineAuthPermission",
    "MachineAPIKeyRateThrottle",
    "MachineAuthViewSet",
]


def __getattr__(name):
    if name == "api_key_module":
        from django_machine_auth.decorators import api_key_module

        return api_key_module
    if name == "MachineAPIKeyAuthentication":
        from django_machine_auth.authentication import MachineAPIKeyAuthentication

        return MachineAPIKeyAuthentication
    if name == "MachineAuthPermission":
        from django_machine_auth.permissions import MachineAuthPermission

        return MachineAuthPermission
    if name == "MachineAPIKeyRateThrottle":
        from django_machine_auth.throttling import MachineAPIKeyRateThrottle

        return MachineAPIKeyRateThrottle
    if name == "MachineAuthViewSet":
        from django_machine_auth.views import MachineAuthViewSet

        return MachineAuthViewSet
    raise AttributeError(name)
