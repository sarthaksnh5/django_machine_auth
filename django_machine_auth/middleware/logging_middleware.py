import json
import time

from django.utils.deprecation import MiddlewareMixin

from django_machine_auth.models import APIKeyRequestLog
from django_machine_auth.utils.settings import logging_mode, request_logging_enabled

SENSITIVE_KEYS = {"authorization", "password", "token", "secret", "api_key"}


def _safe_decode(value):
    if not value:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    try:
        return json.loads(value)
    except Exception:
        return {"raw": str(value)}


def _redact_mapping(data):
    if not isinstance(data, dict):
        return data
    output = {}
    for key, value in data.items():
        if str(key).lower() in SENSITIVE_KEYS:
            output[key] = "***REDACTED***"
        elif isinstance(value, dict):
            output[key] = _redact_mapping(value)
        else:
            output[key] = value
    return output


class MachineAuthLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._machine_auth_started_at = time.monotonic()

    def process_response(self, request, response):
        if not request_logging_enabled():
            return response

        api_key = getattr(request, "machine_api_key", None)
        if not api_key:
            return response

        started = getattr(request, "_machine_auth_started_at", None)
        duration = (time.monotonic() - started) if started else 0.0

        mode = logging_mode()
        headers = dict(request.headers.items())
        request_body = _safe_decode(getattr(request, "body", b""))
        response_body = _safe_decode(getattr(response, "content", b""))

        if mode == "metadata_only":
            headers = {}
            request_body = None
            response_body = None
        elif mode == "redacted":
            headers = _redact_mapping(headers)
            request_body = _redact_mapping(request_body)
            response_body = _redact_mapping(response_body)

        APIKeyRequestLog.objects.create(
            api_key_id=getattr(api_key, "id", None),
            user_id=getattr(request.user, "id", None),
            url=request.build_absolute_uri(),
            method=request.method,
            headers=headers,
            request_body=request_body,
            response_body=response_body,
            status_code=response.status_code,
            ip_address=request.META.get("REMOTE_ADDR"),
            duration=duration,
        )
        return response
