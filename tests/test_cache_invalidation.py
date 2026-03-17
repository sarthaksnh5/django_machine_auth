import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from django_machine_auth.models import MachineAPIKey, MachinePermission
from django_machine_auth.utils.cache import build_cache_key


pytestmark = pytest.mark.django_db


def _seed_perms():
    MachinePermission.objects.get_or_create(module="users", permission="users.view", defaults={"label": "View"})
    MachinePermission.objects.get_or_create(module="users", permission="users.create", defaults={"label": "Create"})


def test_cache_invalidates_when_permissions_change():
    _seed_perms()
    user = get_user_model().objects.create_user(username="cache-user-1")
    key = MachineAPIKey.objects.create(
        name="k",
        user=user,
        hashed_key="1" * 64,
        permissions=["users.view"],
    )
    cache.set(build_cache_key(key.hashed_key), {"v": 1, "permissions": ["users.view"]}, 100)
    key.permissions = ["users.view", "users.create"]
    key.save()
    assert cache.get(build_cache_key(key.hashed_key)) is None


def test_cache_invalidates_when_active_or_expiry_changes():
    _seed_perms()
    user = get_user_model().objects.create_user(username="cache-user-2")
    key = MachineAPIKey.objects.create(
        name="k",
        user=user,
        hashed_key="2" * 64,
        permissions=["users.view"],
        is_active=True,
    )
    cache.set(build_cache_key(key.hashed_key), {"v": 1}, 100)
    key.is_active = False
    key.save()
    assert cache.get(build_cache_key(key.hashed_key)) is None
