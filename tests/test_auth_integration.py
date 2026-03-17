from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from django_machine_auth.models import APIKeyRequestLog, MachineAPIKey, MachinePermission
from django_machine_auth.registry.module_registry import MODULE_REGISTRY, register_module
from django_machine_auth.utils.cache import get_cached_auth_payload
from django_machine_auth.utils.hashing import hash_api_key


pytestmark = pytest.mark.django_db


def _seed_registry():
    MODULE_REGISTRY.clear()
    register_module(
        "users",
        "User Management",
        crud=["view", "create", "update", "delete"],
        actions={"profile": ["get", "post"]},
    )


def _seed_permissions():
    for permission in [
        "users.view",
        "users.create",
        "users.update",
        "users.delete",
        "users.profile.get",
        "users.profile.post",
    ]:
        MachinePermission.objects.get_or_create(
            module="users",
            permission=permission,
            defaults={"label": permission},
        )  # pylint: disable=no-member


def _create_key(user, raw_key, *, active=True, expires_at=None, permissions=None):
    return MachineAPIKey.objects.create(  # pylint: disable=no-member
        name="k1",
        user=user,
        hashed_key=hash_api_key(raw_key),
        is_active=active,
        expires_at=expires_at,
        permissions=permissions or ["users.view"],
    )


@override_settings(ROOT_URLCONF="tests.urls_machine", MACHINE_AUTH={"KEY_PREFIX": "mac_"})
def test_auth_allows_valid_key_and_denies_invalid_prefix():
    _seed_registry()
    _seed_permissions()
    user = get_user_model().objects.create_user(username="u1")
    _create_key(user, "mac_valid123", permissions=["users.view"])
    client = APIClient()

    ok = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_valid123")
    bad = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth bad_valid123")

    assert ok.status_code == 200
    assert bad.status_code == 401


@override_settings(ROOT_URLCONF="tests.urls_machine", MACHINE_AUTH={"KEY_PREFIX": "mac_"})
def test_auth_denies_unknown_inactive_and_expired_keys():
    _seed_registry()
    _seed_permissions()
    user = get_user_model().objects.create_user(username="u2")
    _create_key(user, "mac_inactive", active=False)
    _create_key(user, "mac_expired", expires_at=timezone.now() - timedelta(minutes=1))
    client = APIClient()

    unknown = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_unknown")
    inactive = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_inactive")
    expired = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_expired")

    assert unknown.status_code == 401
    assert inactive.status_code == 401
    assert expired.status_code == 401


@override_settings(ROOT_URLCONF="tests.urls_machine", MACHINE_AUTH={"KEY_PREFIX": "mac_", "CACHE_TIMEOUT": 3600})
def test_auth_populates_cache_and_uses_cached_payload():
    _seed_registry()
    _seed_permissions()
    user = get_user_model().objects.create_user(username="u3")
    key = _create_key(user, "mac_cached", permissions=["users.view"])
    client = APIClient()

    first = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_cached")
    assert first.status_code == 200
    assert get_cached_auth_payload(key.hashed_key) is not None

    # Force DB state to inactive without save() to bypass invalidation and prove cache-path execution.
    MachineAPIKey.objects.filter(pk=key.pk).update(is_active=False)  # pylint: disable=no-member
    second = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_cached")
    assert second.status_code == 200


@override_settings(ROOT_URLCONF="tests.urls_machine", MACHINE_AUTH={"KEY_PREFIX": "mac_"})
def test_permission_mapping_for_crud_and_action_methods():
    _seed_registry()
    _seed_permissions()
    user = get_user_model().objects.create_user(username="u4")
    _create_key(
        user,
        "mac_perm",
        permissions=["users.view", "users.create", "users.profile.get"],
    )
    client = APIClient()

    list_resp = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_perm")
    create_resp = client.post("/machine-users/", {}, format="json", HTTP_AUTHORIZATION="machine_auth mac_perm")
    action_get = client.get("/machine-users/profile/", HTTP_AUTHORIZATION="machine_auth mac_perm")
    action_post = client.post("/machine-users/profile/", {}, format="json", HTTP_AUTHORIZATION="machine_auth mac_perm")

    assert list_resp.status_code == 200
    assert create_resp.status_code == 201
    assert action_get.status_code == 200
    assert action_post.status_code == 403


@override_settings(
    ROOT_URLCONF="tests.urls_machine",
    MACHINE_AUTH={"KEY_PREFIX": "mac_", "ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "metadata_only"},
    MIDDLEWARE=["django_machine_auth.middleware.logging_middleware.MachineAuthLoggingMiddleware"],
)
def test_successful_machine_auth_request_gets_logged():
    _seed_registry()
    _seed_permissions()
    user = get_user_model().objects.create_user(username="u5")
    _create_key(user, "mac_logged", permissions=["users.view"])
    client = APIClient()

    response = client.get("/machine-users/", HTTP_AUTHORIZATION="machine_auth mac_logged")

    assert response.status_code == 200
    assert APIKeyRequestLog.objects.filter(method="GET", status_code=200).exists()  # pylint: disable=no-member
