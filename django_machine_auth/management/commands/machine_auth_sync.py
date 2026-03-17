from django.core.management.base import BaseCommand

from django_machine_auth.models import MachinePermission
from django_machine_auth.registry.module_registry import discover_modules, iter_permission_rows


class Command(BaseCommand):
    help = "Synchronize machine auth permissions from module registry into database"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        discover_modules()

        desired = {(r["module"], r["permission"]): r for r in iter_permission_rows()}
        existing = {(r.module, r.permission): r for r in MachinePermission.objects.all()}

        to_create = sorted(
            (v for k, v in desired.items() if k not in existing),
            key=lambda row: (row["module"], row["permission"]),
        )
        to_delete = sorted(
            (v for k, v in existing.items() if k not in desired),
            key=lambda row: (row.module, row.permission),
        )
        to_update = []
        for key, desired_row in desired.items():
            current = existing.get(key)
            if current and current.label != desired_row["label"]:
                to_update.append((current, desired_row["label"]))
        to_update.sort(key=lambda row: (row[0].module, row[0].permission))

        self.stdout.write("Running Machine Auth Permission Sync")
        if dry_run:
            self.stdout.write("Mode: dry-run")
        for row in to_create:
            self.stdout.write(f"+ Created: {row['permission']}")
            if not dry_run:
                MachinePermission.objects.create(**row)

        for row in to_delete:
            self.stdout.write(f"- Deleted: {row.permission}")
            if not dry_run:
                row.delete()

        for row, label in to_update:
            self.stdout.write(f"~ Updated label: {row.permission}")
            if not dry_run:
                row.label = label
                row.save(update_fields=["label"])

        if not to_create and not to_delete and not to_update:
            self.stdout.write("No changes detected.")
        self.stdout.write(self.style.SUCCESS("Sync Complete"))
