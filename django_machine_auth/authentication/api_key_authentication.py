from dataclasses import dataclass
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from django_machine_auth.models import MachineAPIKey
from django_machine_auth.utils.cache import get_cached_auth_payload, set_cached_auth_payload
from django_machine_auth.utils.hashing import hash_api_key
from django_machine_auth.utils.settings import key_prefix


@dataclass
class CachedMachineKey:
    id: int
    user_id: int
    permissions: list
    expires_at: str
    is_active: bool


class MachineAPIKeyAuthentication(authentication.BaseAuthentication):
    keyword = "machine_auth"
    payload_version = 1

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        try:
            scheme, raw_key = auth_header.split(" ", 1)
        except ValueError as exc:
            raise AuthenticationFailed("Invalid authorization header format") from exc

        if scheme.lower() != self.keyword:
            return None

        expected_prefix = key_prefix()
        if not raw_key.startswith(expected_prefix):
            raise AuthenticationFailed("Invalid machine API key prefix")

        hashed_key = hash_api_key(raw_key)
        payload = get_cached_auth_payload(hashed_key)
        if payload:
            if payload.get("v") != self.payload_version:
                payload = None
        if payload:
            expires_at = payload.get("expires_at")
            if expires_at and datetime.fromisoformat(expires_at) <= timezone.now():
                raise AuthenticationFailed("Machine API key has expired")
            if not payload.get("is_active"):
                raise AuthenticationFailed("Machine API key is inactive")

            User = get_user_model()
            user = User.objects.filter(pk=payload["user_id"]).first()
            if not user:
                raise AuthenticationFailed("Machine API key user does not exist")

            machine_key = CachedMachineKey(
                id=payload["id"],
                user_id=payload["user_id"],
                permissions=payload.get("permissions", []),
                expires_at=expires_at,
                is_active=payload.get("is_active", True),
            )
            self._attach_machine_key(request, machine_key)
            MachineAPIKey.objects.filter(pk=payload["id"]).update(last_used_at=timezone.now())  # pylint: disable=no-member
            return user, machine_key

        api_key = MachineAPIKey.objects.select_related("user").filter(hashed_key=hashed_key).first()  # pylint: disable=no-member
        if not api_key:
            raise AuthenticationFailed("Invalid machine API key")
        if not api_key.is_active:
            raise AuthenticationFailed("Machine API key is inactive")
        if api_key.is_expired:
            raise AuthenticationFailed("Machine API key has expired")

        set_cached_auth_payload(
            hashed_key,
            {
                "v": self.payload_version,
                "id": api_key.id,
                "user_id": api_key.user_id,
                "permissions": api_key.permissions,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "is_active": api_key.is_active,
            },
        )
        MachineAPIKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())  # pylint: disable=no-member
        self._attach_machine_key(request, api_key)
        return api_key.user, api_key

    def authenticate_header(self, request):
        return self.keyword

    @staticmethod
    def _attach_machine_key(request, machine_key):
        request.machine_api_key = machine_key
        # Middleware runs against Django HttpRequest (`request._request` in DRF views).
        # Mirror this attribute so logging middleware can reliably detect machine-auth context.
        if hasattr(request, "_request"):
            request._request.machine_api_key = machine_key
