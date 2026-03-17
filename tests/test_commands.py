from io import StringIO

import pytest
from django.core.management import call_command

from django_machine_auth.models import MachinePermission
from django_machine_auth.registry.module_registry import MODULE_REGISTRY, register_module


pytestmark = pytest.mark.django_db


def _register_users_module():
    MODULE_REGISTRY.clear()
    register_module(
        "users",
        "User Management",
        crud=["view", "create", "update", "delete"],
        actions={"profile": ["get", "post"]},
    )


def test_machine_auth_sync_create_delete_update_and_dry_run():
    _register_users_module()
    stale = MachinePermission.objects.create(
        module="users",
        permission="users.old_permission.post",
        label="Old",
    )
    needs_update = MachinePermission.objects.create(
        module="users",
        permission="users.view",
        label="Wrong Label",
    )

    stdout = StringIO()
    call_command("machine_auth_sync", stdout=stdout)
    output = stdout.getvalue()

    assert "+ Created: users.create" in output
    assert "- Deleted: users.old_permission.post" in output
    assert "~ Updated label: users.view" in output
    assert not MachinePermission.objects.filter(pk=stale.pk).exists()
    needs_update.refresh_from_db()
    assert needs_update.label == "View"

    before = MachinePermission.objects.count()
    dry_stdout = StringIO()
    call_command("machine_auth_sync", "--dry-run", stdout=dry_stdout)
    dry_output = dry_stdout.getvalue()
    after = MachinePermission.objects.count()

    assert "Mode: dry-run" in dry_output
    assert "No changes detected." in dry_output
    assert before == after


def test_machine_auth_permissions_command_prints_grouped_output():
    _register_users_module()
    stdout = StringIO()
    call_command("machine_auth_permissions", stdout=stdout)
    output = stdout.getvalue()

    assert "Machine Auth Permission Documentation" in output
    assert "Module: User Management (users)" in output
    assert "CRUD Permissions" in output
    assert "Action Permissions" in output
    assert "users.profile.get" in output
