from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from django_machine_auth.models import MachineAPIKey, MachinePermission
from django_machine_auth.utils.hashing import hash_api_key


pytestmark = pytest.mark.django_db


@override_settings(ROOT_URLCONF="tests.urls_admin_tokens")
def test_superuser_can_create_machine_api_key_for_any_user():
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    MachinePermission.objects.create(module="users", permission="users.create", label="Create")
    user_model = get_user_model()
    admin = user_model.objects.create_superuser(username="admin", email="admin@test.com", password="admin")
    owner = user_model.objects.create_user(username="owner")
    client = APIClient()
    client.force_authenticate(user=admin)
    expires_at = (timezone.now() + timedelta(days=10)).isoformat()

    response = client.post(
        "/machine-api-keys/",
        {
            "name": "Gov Portal",
            "user": owner.id,
            "expires_at": expires_at,
            "permissions": ["users.view", "users.create"],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["name"] == "Gov Portal"
    assert response.data["user"] == owner.id
    assert response.data["raw_api_key"].startswith("mac_")
    assert response.data["permissions"] == ["users.view", "users.create"]

    created = MachineAPIKey.objects.get(pk=response.data["id"])  # pylint: disable=no-member
    assert created.user_id == owner.id
    assert created.hashed_key == hash_api_key(response.data["raw_api_key"])


@override_settings(ROOT_URLCONF="tests.urls_admin_tokens")
def test_authenticated_user_can_create_key_for_self_only():
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    user_model = get_user_model()
    normal_user = user_model.objects.create_user(username="u1")
    other = user_model.objects.create_user(username="owner2")
    client = APIClient()
    client.force_authenticate(user=normal_user)

    own = client.post(
        "/machine-api-keys/",
        {"name": "My Portal", "user": normal_user.id, "permissions": ["users.view"]},
        format="json",
    )
    other_user = client.post(
        "/machine-api-keys/",
        {"name": "Contractor Portal", "user": other.id, "permissions": ["users.view"]},
        format="json",
    )

    assert own.status_code == 201
    assert other_user.status_code == 400


@override_settings(ROOT_URLCONF="tests.urls_admin_tokens")
def test_create_rejects_invalid_permissions():
    user_model = get_user_model()
    admin = user_model.objects.create_superuser(username="admin2", email="admin2@test.com", password="admin")
    owner = user_model.objects.create_user(username="owner3")
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(
        "/machine-api-keys/",
        {"name": "Bad Key", "user": owner.id, "permissions": ["users.unknown"]},
        format="json",
    )
    assert response.status_code == 400
    assert "Invalid permissions:" in str(response.data)
