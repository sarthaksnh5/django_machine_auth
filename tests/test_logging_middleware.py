import json

import pytest
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, override_settings

from django_machine_auth.middleware.logging_middleware import MachineAuthLoggingMiddleware
from django_machine_auth.models import APIKeyRequestLog, MachineAPIKey


pytestmark = pytest.mark.django_db


def _build_request(user, *, auth_header="machine_auth mac_test"):
    factory = RequestFactory()
    request = factory.post(
        "/machine",
        data=json.dumps({"password": "secret", "name": "ok"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_header,
    )
    request.user = user
    return request


def _attach_machine_key(user):
    return MachineAPIKey.objects.create(
        name="log-key",
        user=user,
        hashed_key="a" * 64,
        permissions=["users.view"],
    )


@override_settings(MACHINE_AUTH={"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "raw"})
def test_logging_raw_mode_stores_payloads():
    user = get_user_model().objects.create_user(username="log-raw")
    request = _build_request(user)
    request.machine_api_key = _attach_machine_key(user)
    response = JsonResponse({"token": "abc"})
    middleware = MachineAuthLoggingMiddleware(get_response=lambda r: response)

    middleware.process_request(request)
    middleware.process_response(request, response)

    log = APIKeyRequestLog.objects.latest("id")
    assert log.request_body["password"] == "secret"
    assert log.response_body["token"] == "abc"


@override_settings(MACHINE_AUTH={"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "redacted"})
def test_logging_redacted_mode_masks_sensitive_fields():
    user = get_user_model().objects.create_user(username="log-redacted")
    request = _build_request(user)
    request.machine_api_key = _attach_machine_key(user)
    response = JsonResponse({"secret": "abc", "ok": True})
    middleware = MachineAuthLoggingMiddleware(get_response=lambda r: response)

    middleware.process_request(request)
    middleware.process_response(request, response)

    log = APIKeyRequestLog.objects.latest("id")
    assert log.request_body["password"] == "***REDACTED***"
    assert log.response_body["secret"] == "***REDACTED***"
    assert log.headers["Authorization"] == "***REDACTED***"


@override_settings(MACHINE_AUTH={"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "metadata_only"})
def test_logging_metadata_only_mode_skips_payloads():
    user = get_user_model().objects.create_user(username="log-meta")
    request = _build_request(user)
    request.machine_api_key = _attach_machine_key(user)
    response = JsonResponse({"ok": True})
    middleware = MachineAuthLoggingMiddleware(get_response=lambda r: response)

    middleware.process_request(request)
    middleware.process_response(request, response)

    log = APIKeyRequestLog.objects.latest("id")
    assert log.request_body is None
    assert log.response_body is None
    assert log.headers == {}


@override_settings(MACHINE_AUTH={"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "bad_value"})
def test_invalid_logging_mode_falls_back_to_redacted():
    user = get_user_model().objects.create_user(username="log-fallback")
    request = _build_request(user)
    request.machine_api_key = _attach_machine_key(user)
    response = JsonResponse({"api_key": "abc"})
    middleware = MachineAuthLoggingMiddleware(get_response=lambda r: response)

    middleware.process_request(request)
    middleware.process_response(request, response)

    log = APIKeyRequestLog.objects.latest("id")
    assert log.response_body["api_key"] == "***REDACTED***"


@override_settings(MACHINE_AUTH={"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "raw"})
def test_non_machine_request_is_skipped():
    user = get_user_model().objects.create_user(username="log-skip")
    request = _build_request(user)
    response = JsonResponse({"ok": True})
    middleware = MachineAuthLoggingMiddleware(get_response=lambda r: response)

    middleware.process_request(request)
    middleware.process_response(request, response)

    assert APIKeyRequestLog.objects.count() == 0
