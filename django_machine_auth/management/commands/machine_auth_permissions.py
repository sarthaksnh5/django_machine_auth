from django.core.management.base import BaseCommand

from django_machine_auth.registry.module_registry import discover_modules, get_registry


class Command(BaseCommand):
    help = "Print machine auth permission documentation"

    def handle(self, *args, **options):
        discover_modules()
        registry = get_registry()

        self.stdout.write("Machine Auth Permission Documentation")
        for module_name in sorted(registry.keys()):
            module = registry[module_name]
            self.stdout.write("")
            self.stdout.write(f"Module: {module['label']} ({module_name})")
            self.stdout.write("CRUD Permissions")
            for crud in module.get("crud", []):
                self.stdout.write(f"{module_name}.{crud}")
            self.stdout.write("")
            self.stdout.write("Action Permissions")
            action_perms = []
            for action_name, methods in sorted(module.get("actions", {}).items()):
                for method in methods:
                    action_perms.append(f"{module_name}.{action_name}.{method}")
            for permission in sorted(action_perms):
                self.stdout.write(permission)
