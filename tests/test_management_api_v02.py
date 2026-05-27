from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from django_machine_auth.models import MachineAPIKey, MachinePermission
from django_machine_auth.utils.hashing import hash_api_key


pytestmark = pytest.mark.django_db


def _seed_permissions():
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    MachinePermission.objects.create(module="users", permission="users.create", label="Create")
    MachinePermission.objects.create(module="complaint", permission="complaint.view", label="Complaint View")


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_permission_catalog_filters():
    _seed_permissions()
    user = get_user_model().objects.create_user(username="perm-user")
    client = APIClient()
    client.force_authenticate(user=user)

    module_resp = client.get("/machine-auth/permissions/?module=users")
    search_resp = client.get("/machine-auth/permissions/?search=complaint")

    assert module_resp.status_code == 200
    assert len(module_resp.data) == 2
    assert search_resp.status_code == 200
    assert len(search_resp.data) == 1
    assert search_resp.data[0]["permission"] == "complaint.view"


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_superuser_lists_all_keys_normal_user_lists_own_only():
    _seed_permissions()
    user_model = get_user_model()
    superuser = user_model.objects.create_superuser(username="su", email="su@test.com", password="su")
    u1 = user_model.objects.create_user(username="u1")
    u2 = user_model.objects.create_user(username="u2")

    MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="k1", user=u1, hashed_key="a" * 64, permissions=["users.view"]
    )
    MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="k2", user=u2, hashed_key="b" * 64, permissions=["users.view"]
    )

    su_client = APIClient()
    su_client.force_authenticate(user=superuser)
    assert su_client.get("/machine-auth/machine-api-keys/").status_code == 200
    assert len(su_client.get("/machine-auth/machine-api-keys/").data) == 2

    u1_client = APIClient()
    u1_client.force_authenticate(user=u1)
    u1_list = u1_client.get("/machine-auth/machine-api-keys/")
    assert u1_list.status_code == 200
    assert len(u1_list.data) == 1
    assert u1_list.data[0]["name"] == "k1"


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_retrieve_includes_permissions_and_blocks_other_users_key():
    _seed_permissions()
    user_model = get_user_model()
    u1 = user_model.objects.create_user(username="owner1")
    u2 = user_model.objects.create_user(username="owner2")
    key = MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="owner-key",
        user=u1,
        hashed_key="c" * 64,
        permissions=["users.view", "users.create"],
    )

    u2_client = APIClient()
    u2_client.force_authenticate(user=u2)
    assert u2_client.get(f"/machine-auth/machine-api-keys/{key.id}/").status_code == 404

    u1_client = APIClient()
    u1_client.force_authenticate(user=u1)
    detail = u1_client.get(f"/machine-auth/machine-api-keys/{key.id}/")
    assert detail.status_code == 200
    assert detail.data["permissions"] == ["users.view", "users.create"]


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_user_can_create_key_for_self_not_for_others():
    _seed_permissions()
    user_model = get_user_model()
    u1 = user_model.objects.create_user(username="creator")
    u2 = user_model.objects.create_user(username="other")
    client = APIClient()
    client.force_authenticate(user=u1)

    own = client.post(
        "/machine-auth/machine-api-keys/",
        {"name": "My Key", "user": u1.id, "permissions": ["users.view"]},
        format="json",
    )
    other = client.post(
        "/machine-auth/machine-api-keys/",
        {"name": "Other Key", "user": u2.id, "permissions": ["users.view"]},
        format="json",
    )

    assert own.status_code == 201
    assert other.status_code == 400


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_superuser_can_create_for_any_user():
    _seed_permissions()
    user_model = get_user_model()
    superuser = user_model.objects.create_superuser(username="su2", email="su2@test.com", password="su2")
    owner = user_model.objects.create_user(username="target")
    client = APIClient()
    client.force_authenticate(user=superuser)

    response = client.post(
        "/machine-auth/machine-api-keys/",
        {"name": "Assigned", "user": owner.id, "permissions": ["users.view"]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["user"] == owner.id


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_update_permissions_and_deactivate():
    _seed_permissions()
    user_model = get_user_model()
    user = user_model.objects.create_user(username="updater")
    raw = "mac_updater_key"
    key = MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="updatable",
        user=user,
        hashed_key=hash_api_key(raw),
        permissions=["users.view"],
        is_active=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    patch_resp = client.patch(
        f"/machine-auth/machine-api-keys/{key.id}/",
        {"permissions": ["users.view", "users.create"]},
        format="json",
    )
    assert patch_resp.status_code == 200

    deactivate_resp = client.post(f"/machine-auth/machine-api-keys/{key.id}/deactivate/")
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.data["is_active"] is False
