import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from django_machine_auth.admin.api_key_admin import MachineAPIKeyAdminForm
from django_machine_auth.models import MachinePermission


pytestmark = pytest.mark.django_db


def test_admin_form_groups_permissions_and_filters_by_search():
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    MachinePermission.objects.create(module="orders", permission="orders.view", label="View")
    request = RequestFactory().get("/admin", {"permission_search": "users"})

    form = MachineAPIKeyAdminForm(request=request)
    groups = dict(form.fields["permissions"].choices)

    assert "users" in groups
    assert "orders" not in groups


def test_admin_form_rejects_invalid_permission_submission():
    user = get_user_model().objects.create_user(username="admin-form-user")
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    request = RequestFactory().post("/admin")
    form = MachineAPIKeyAdminForm(
        data={
            "name": "new key",
            "user": user.pk,
            "permissions": ["users.bad_permission"],
            "is_active": True,
        },
        request=request,
    )

    assert not form.is_valid()
    assert "permissions" in form.errors
