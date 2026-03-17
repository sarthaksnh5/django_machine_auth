import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from django_machine_auth.models import MachinePermission


pytestmark = pytest.mark.django_db


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_package_url_include_exposes_machine_api_key_endpoint():
    user_model = get_user_model()
    admin = user_model.objects.create_superuser(username="root", email="root@test.com", password="root")
    owner = user_model.objects.create_user(username="ownerx")
    MachinePermission.objects.create(module="users", permission="users.view", label="View")
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(
        "/machine-auth/machine-api-keys/",
        {"name": "Portal", "user": owner.id, "permissions": ["users.view"]},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["raw_api_key"].startswith("mac_")
