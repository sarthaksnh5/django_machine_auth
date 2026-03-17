# django_machine_auth

`django_machine_auth` is a machine-to-machine authentication framework for Django REST Framework using API keys and module-scoped permissions.

## Navigation

- Quickstart: install, configure, define module, protect viewset
- Architecture: auth flow, permission resolution, and sync model
- Operations: rotation, logging mode, and monitoring guidance
- Troubleshooting: common setup and runtime issues

## Features

- API key auth with `Authorization: machine_auth <api_key>`
- Module-driven permission model (`module.crud` + `module.action.method`)
- SHA256 key storage (raw keys are never persisted)
- Cache-first authentication payload lookups
- DB-backed permission registry (`MachinePermission`)
- Permission sync and documentation commands
- Optional request logging middleware with configurable privacy mode
- DRF-compatible throttling and permission classes

## Installation

```bash
pip install django_machine_auth
```

## Configure Django

Add app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_machine_auth",
]
```

Optional settings:

```python
MACHINE_AUTH = {
    "KEY_PREFIX": "mac_",                 # default: mac_
    "ENABLE_REQUEST_LOGGING": False,      # default: False
    "LOGGING_MODE": "redacted",           # raw | redacted | metadata_only
    "CACHE_TIMEOUT": 3600,                # default: 3600 seconds
}
```

## Define module permissions

Create `<your_app>/api_key_perm.py`:

```python
from django_machine_auth.decorators import api_key_module


@api_key_module("users", label="User Management")
class UsersModule:
    crud = ["view", "create", "update", "delete"]
    actions = {
        "profile": ["get", "post"],
    }
```

## Protect DRF endpoints

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from django_machine_auth.views import MachineAuthViewSet


class UserMachineViewSet(MachineAuthViewSet):
    module = "users"

    def list(self, request):
        return Response({"ok": True})

    @action(detail=False, methods=["get"])
    def profile(self, request):
        return Response({"ok": True})
```

## Permission mapping

- `list`, `retrieve` -> `module.view`
- `create` -> `module.create`
- `update`, `partial_update` -> `module.update`
- `destroy` -> `module.delete`
- Custom action -> `module.<action>.<http_method_lower>`

## Management commands

Sync code-defined permissions into DB:

```bash
python manage.py machine_auth_sync
python manage.py machine_auth_sync --dry-run
```

Print permission documentation:

```bash
python manage.py machine_auth_permissions
```

## Admin token creation API (DRF)

Use `MachineAPIKeyManagementViewSet` for admin-only key issuance.

Simplest URL wiring:

```python
from django.urls import include, path

urlpatterns = [
    path("machine-auth/", include("django_machine_auth.urls")),
]
```

This exposes:

- `POST /machine-auth/machine-api-keys/`

Required request fields:

- `name`
- `user` (user id)
- `permissions` (list of permission strings from `MachinePermission`)

Optional:

- `expires_at`

Example request payload:

```json
{
  "name": "Gov Portal",
  "user": 5,
  "permissions": ["users.view", "users.create"],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

Response includes `raw_api_key` once. Store it securely; only hash is persisted.

## Architecture overview

Runtime request flow:

1. `MachineAPIKeyAuthentication` parses and validates auth header.
2. Hash lookup checks cache first, then DB fallback.
3. `MachineAuthPermission` resolves action/method permission.
4. `MachineAPIKeyRateThrottle` applies per-key throttle scope.
5. Optional `MachineAuthLoggingMiddleware` writes request log entry.

## Logging modes

- `raw`: stores full request/response payload snapshots
- `redacted`: masks sensitive keys (`authorization`, `password`, `token`, `secret`, `api_key`)
- `metadata_only`: stores only metadata (status, url, method, timing, ip)

Enable middleware when needed:

```python
MIDDLEWARE = [
    # ...
    "django_machine_auth.middleware.logging_middleware.MachineAuthLoggingMiddleware",
]
```

## Security and operations

- Rotate API keys periodically.
- Use short expiry windows for integration keys where possible.
- Keep logging mode as `redacted` or `metadata_only` in production.
- Run `machine_auth_sync` as part of deploy/startup checks after module permission changes.

Detailed operations guide: `docs/OPERATIONS.md`.

## Troubleshooting

- `No default throttle rate set for 'machine_api_key'`:
  - Add `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES.machine_api_key`.
- `Module '<name>' used by <ViewSet> is not registered`:
  - Ensure `<app>/api_key_perm.py` exists and module name matches `view.module`.
- `Action "<action>" ... not defined in module`:
  - Add action/method mapping in `api_key_perm.py`.
- Permission denied for custom action:
  - Confirm API key includes exact `module.action.method` string.

## Local test workflow

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/pytest -q
```

## Release and upgrade docs

- Changelog: `CHANGELOG.md`
- Upgrade guide: `UPGRADING.md`
