import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from django_machine_auth.models import APIKeyRequestLog, MachineAPIKey
from django_machine_auth.utils.hashing import hash_api_key


pytestmark = pytest.mark.django_db


def _create_key(user, name="key"):
    return MachineAPIKey.objects.create(  # pylint: disable=no-member
        name=name,
        user=user,
        hashed_key=hash_api_key(f"test-key-{name}-{user.id}"),
        permissions=["users.view"],
    )


def _create_log(api_key, user, url="/test/"):
    return APIKeyRequestLog.objects.create(  # pylint: disable=no-member
        api_key=api_key,
        user=user,
        url=url,
        method="GET",
        headers={},
        status_code=200,
        duration=0.01,
    )


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_superuser_lists_all_and_filters_by_user():
    user_model = get_user_model()
    superuser = user_model.objects.create_superuser(username="su-log", email="su@test.com", password="su")
    u1 = user_model.objects.create_user(username="log-u1")
    u2 = user_model.objects.create_user(username="log-u2")
    k1 = _create_key(u1, "k1")
    k2 = _create_key(u2, "k2")
    _create_log(k1, u1, url="/u1/")
    _create_log(k2, u2, url="/u2/")

    client = APIClient()
    client.force_authenticate(user=superuser)

    all_resp = client.get("/machine-auth/request-logs/")
    assert all_resp.status_code == 200
    assert len(all_resp.data) == 2

    u1_resp = client.get(f"/machine-auth/request-logs/?user={u1.id}")
    assert u1_resp.status_code == 200
    assert len(u1_resp.data) == 1
    assert u1_resp.data[0]["url"] == "/u1/"


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_superuser_filters_by_api_key():
    user_model = get_user_model()
    superuser = user_model.objects.create_superuser(username="su-log2", email="su2@test.com", password="su2")
    owner = user_model.objects.create_user(username="log-owner")
    k1 = _create_key(owner, "k-a")
    k2 = _create_key(owner, "k-b")
    _create_log(k1, owner, url="/a/")
    _create_log(k2, owner, url="/b/")

    client = APIClient()
    client.force_authenticate(user=superuser)

    resp = client.get(f"/machine-auth/request-logs/?api_key={k1.id}")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["url"] == "/a/"


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_user_sees_only_own_key_logs():
    user_model = get_user_model()
    u1 = user_model.objects.create_user(username="viewer1")
    u2 = user_model.objects.create_user(username="viewer2")
    k1 = _create_key(u1)
    k2 = _create_key(u2)
    log1 = _create_log(k1, u1)
    _create_log(k2, u2)

    client = APIClient()
    client.force_authenticate(user=u1)
    resp = client.get("/machine-auth/request-logs/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["id"] == log1.id


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_user_filter_own_api_key_and_forbidden_for_others():
    user_model = get_user_model()
    u1 = user_model.objects.create_user(username="viewer3")
    u2 = user_model.objects.create_user(username="viewer4")
    k1 = _create_key(u1)
    k2 = _create_key(u2)
    _create_log(k1, u1, url="/mine/")
    _create_log(k2, u2, url="/theirs/")

    client = APIClient()
    client.force_authenticate(user=u1)

    own = client.get(f"/machine-auth/request-logs/?api_key={k1.id}")
    assert own.status_code == 200
    assert len(own.data) == 1
    assert own.data[0]["url"] == "/mine/"

    forbidden = client.get(f"/machine-auth/request-logs/?api_key={k2.id}")
    assert forbidden.status_code == 403


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_retrieve_detail_includes_bodies_and_blocks_other_user():
    user_model = get_user_model()
    u1 = user_model.objects.create_user(username="detail-u1")
    u2 = user_model.objects.create_user(username="detail-u2")
    k1 = _create_key(u1)
    log = _create_log(k1, u1)
    log.headers = {"x-test": "1"}
    log.request_body = {"a": 1}
    log.response_body = {"b": 2}
    log.save()

    u1_client = APIClient()
    u1_client.force_authenticate(user=u1)
    detail = u1_client.get(f"/machine-auth/request-logs/{log.id}/")
    assert detail.status_code == 200
    assert detail.data["headers"] == {"x-test": "1"}
    assert detail.data["request_body"] == {"a": 1}
    assert "request_body" not in u1_client.get("/machine-auth/request-logs/").data[0]

    u2_client = APIClient()
    u2_client.force_authenticate(user=u2)
    assert u2_client.get(f"/machine-auth/request-logs/{log.id}/").status_code == 404


@override_settings(ROOT_URLCONF="tests.urls_package_include")
def test_unauthenticated_denied():
    client = APIClient()
    assert client.get("/machine-auth/request-logs/").status_code == 403
