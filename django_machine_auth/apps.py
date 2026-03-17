from django.apps import AppConfig


class DjangoMachineAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_machine_auth"

    def ready(self):
        from django_machine_auth.registry.module_registry import discover_modules
        from django_machine_auth.views.validation import validate_machine_viewsets

        discover_modules()
        validate_machine_viewsets()
