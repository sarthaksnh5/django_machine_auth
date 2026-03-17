# django_machine_auth Setup and Usage Guide

This guide explains everything required to install, configure, and use `django_machine_auth` in a Django REST Framework project.

---

## 1) What this package does

`django_machine_auth` provides machine-to-machine authentication using API keys with module-based permissions.

Core behavior:

- API key auth via `Authorization: machine_auth <api_key>`
- Permissions like:
  - `users.view`
  - `users.create`
  - `users.profile.get`
- DB-backed permission registry (`MachinePermission`)
- Permission sync command (`machine_auth_sync`)
- Optional request logging middleware
- DRF throttle integration

---

## 2) Requirements

Minimum supported stack:

- Python `>= 3.9`
- Django `>= 3.2`
- Django REST Framework `>= 3.13`

Install dependency:

```bash
pip install django_machine_auth
```

For local development/testing:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
```

---

## 3) Add app to Django

In your Django `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django_machine_auth",
]
```

---

## 4) Configure settings

Add optional config block:

```python
MACHINE_AUTH = {
    "KEY_PREFIX": "mac_",                 # default: mac_
    "ENABLE_REQUEST_LOGGING": False,      # default: False
    "LOGGING_MODE": "redacted",           # raw | redacted | metadata_only
    "CACHE_TIMEOUT": 3600,                # seconds, default: 3600
}
```

What each setting does:

- `KEY_PREFIX`:
  - required prefix for incoming API keys
  - if omitted or empty, defaults to `mac_`
- `ENABLE_REQUEST_LOGGING`:
  - enables/disables machine request logging middleware behavior
- `LOGGING_MODE`:
  - `raw`: log full request/response payloads
  - `redacted`: mask sensitive fields
  - `metadata_only`: no bodies, minimal metadata only
- `CACHE_TIMEOUT`:
  - auth payload cache TTL for faster repeated key validation

---

## 5) Configure DRF throttle scope

Because the package uses a dedicated throttle scope (`machine_api_key`), define a rate:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "machine_api_key": "1000/hour",
    }
}
```

You can tune this per deployment profile.

---

## 6) Create module permission definitions

For each app you want to protect, create `<app_name>/api_key_perm.py`.

Example: `users/api_key_perm.py`

```python
from django_machine_auth.decorators import api_key_module


@api_key_module("users", label="User Management")
class UsersModule:
    crud = ["view", "create", "update", "delete"]
    actions = {
        "profile": ["get", "post"],
        "reset_password": ["post"],
    }
```

Generated permissions include:

- `users.view`
- `users.create`
- `users.update`
- `users.delete`
- `users.profile.get`
- `users.profile.post`
- `users.reset_password.post`

Important:

- If `api_key_perm.py` is missing in an app, discovery skips it safely.
- Custom viewset actions must be declared in module actions; startup validation checks this.

---

## 7) Sync permissions to database

After defining/updating modules, run:

```bash
python manage.py machine_auth_sync
```

Dry run:

```bash
python manage.py machine_auth_sync --dry-run
```

What it does:

- creates missing permissions
- deletes obsolete permissions
- updates permission labels

This keeps code registry and DB registry in sync.

---

## 8) Protect DRF endpoints

Use `MachineAuthViewSet` as your base class and set `module`.

```python
from rest_framework.decorators import action
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class UserMachineViewSet(MachineAuthViewSet):
    module = "users"

    def list(self, request):
        return Response({"ok": True})

    def create(self, request):
        return Response({"created": True}, status=201)

    @action(detail=False, methods=["get", "post"])
    def profile(self, request):
        return Response({"method": request.method})
```

Built-in action mapping:

- `list`, `retrieve` -> `module.view`
- `create` -> `module.create`
- `update`, `partial_update` -> `module.update`
- `destroy` -> `module.delete`
- custom action -> `module.<action>.<method>`

---

## 9) Add routing

Example router setup:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UserMachineViewSet

router = DefaultRouter()
router.register("machine-users", UserMachineViewSet, basename="machine-users")

urlpatterns = [
    path("", include(router.urls)),
]
```

---

## 10) Create machine API keys

Use Django admin:

1. Open admin and create a `MachineAPIKey`.
2. Assign owner user.
3. Select permissions (from DB registry).
4. Optionally set expiry.
5. Save.

Important:

- Raw key is shown once at creation.
- Only hashed key is stored in database.
- Permission assignment is validated against `MachinePermission`.

---

## 11) Create machine API keys via DRF (admin-only)

This package also provides an admin-only viewset:

- `MachineAPIKeyManagementViewSet`

Use this when you want to issue keys programmatically from an internal/admin API.

### Route setup (required)

Recommended simple setup in main project `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("machine-auth/", include("django_machine_auth.urls")),
]
```

This exposes:

- `POST /machine-auth/machine-api-keys/`

Alternative (custom router wiring)

If you prefer full control, you can still register the viewset manually in your own router.

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django_machine_auth.views import MachineAPIKeyManagementViewSet

router = DefaultRouter()
router.register("machine-api-keys", MachineAPIKeyManagementViewSet, basename="machine-api-keys")

urlpatterns = [
    path("api/", include(router.urls)),
]
```

Authentication note:

- This endpoint uses DRF `IsAdminUser`, so your project-level DRF auth (session/JWT/token/etc.) should authenticate an admin user before create is allowed.

Required request fields:

- `name`
- `user` (target owner user id)
- `permissions` (non-empty list of permission strings)

Optional:

- `expires_at`

Example request:

```http
POST /machine-api-keys/
Content-Type: application/json
Authorization: <your admin user auth>
```

```json
{
  "name": "Gov Portal",
  "user": 5,
  "permissions": ["users.view", "users.create"],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

Response:

- includes generated `raw_api_key` once
- stores only `hashed_key` in DB
- rejects non-admin users (`403`)
- rejects unknown permissions (`400`)

---

## 12) Make authenticated requests

Header format:

```text
Authorization: machine_auth <api_key>
```

Example:

```bash
curl -H "Authorization: machine_auth mac_xxxxx" \
  http://127.0.0.1:8000/machine-users/
```

If the key lacks required permission, response is denied (`403`).
If auth is invalid/expired/inactive, response is unauthorized (`401`).

---

## 13) Optional request logging middleware

Add middleware only if request logging is needed:

```python
MIDDLEWARE = [
    # ...
    "django_machine_auth.middleware.logging_middleware.MachineAuthLoggingMiddleware",
]
```

Behavior:

- logs only machine-authenticated requests
- respects `LOGGING_MODE`
- captures URL, method, status, duration, IP, and optional payload snapshots

Recommended:

- `redacted` for most production environments
- `metadata_only` for strict data-minimization environments

---

## 14) Permission documentation command

To print generated permissions for developers/integrators:

```bash
python manage.py machine_auth_permissions
```

---

## 15) Startup validation behavior

At app startup, package validates:

- `MachineAuthViewSet.module` exists and is registered
- custom actions in viewset are declared in module action definitions
- custom action HTTP methods are declared in module definition

If not, it raises `MachineAuthConfigurationError` with an actionable message.

---

## 16) Caching behavior

Auth payloads are cached using hashed key identity for performance.

Cache includes:

- key id
- user id
- permission list
- expiry timestamp
- active flag
- payload version

Cache is invalidated when key-relevant fields change (permissions, active status, expiry, hash) or key is deleted.

---

## 17) Operational best practices

- Rotate machine keys regularly.
- Use key expiry for external integrations.
- Keep permission scope minimal (least privilege).
- Keep logging non-raw in production unless debugging incident.
- Run `machine_auth_sync` on deploy when permission modules change.
- Monitor:
  - auth failures
  - permission denials
  - throttle rejections
  - unusually high per-key traffic

---

## 18) Troubleshooting

### Error: `No default throttle rate set for 'machine_api_key'`

Add:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "machine_api_key": "1000/hour",
    }
}
```

### Error: module not registered

- Check `<app>/api_key_perm.py` exists.
- Ensure `view.module` exactly matches registered module name.
- Ensure app is included in `INSTALLED_APPS`.

### Error: custom action not declared

- Add action + methods to module `actions` map in `api_key_perm.py`.

### Unexpected permission denied

- Verify assigned permissions on API key include exact string:
  - e.g. `users.profile.post` (method-specific)

---

## 19) Useful project files

- Core docs: `README.md`
- Changelog: `CHANGELOG.md`
- Upgrade guide: `UPGRADING.md`
- Ops playbook: `docs/OPERATIONS.md`
- Migration notes: `docs/MIGRATIONS.md`
- Release checklist: `docs/RELEASE_CHECKLIST.md`
- Example app: `examples/basic_project/`

---

## 20) Local validation checklist

```bash
# 1. install
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"

# 2. run tests
.venv/bin/pytest -q

# 3. build package
.venv/bin/python -m build
```

If all pass, setup is healthy.
