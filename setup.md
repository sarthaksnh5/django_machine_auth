# django_machine_auth — Setup and Usage Guide

Complete guide for integrating API key authentication in Django REST Framework.

---

## Table of contents

1. [What this package does](#1-what-this-package-does)
2. [Requirements](#2-requirements)
3. [Add app and settings](#3-add-app-and-settings)
4. [Viewsets overview (read this first)](#4-viewsets-overview-read-this-first)
5. [Part I — Define permissions in code](#part-i--define-permissions-in-code)
6. [Part II — Protect your APIs (`MachineAuthViewSet`)](#part-ii--protect-your-apis-machineauthviewset)
7. [Part III — Permission catalog API (`MachinePermissionViewSet`)](#part-iii--permission-catalog-api-machinepermissionviewset)
8. [Part IV — API key management](#part-iv--api-key-management)
9. [Part V — Call protected APIs with an API key](#part-v--call-protected-apis-with-an-api-key)
10. [Part VII — Request logs API (`MachineAPIKeyRequestLogViewSet`)](#part-vii--request-logs-api-machineapikeyrequestlogviewset)
11. [Part VI — Logging, commands, and troubleshooting](#part-vi--logging-commands-and-troubleshooting)

---

## 1) What this package does

`django_machine_auth` lets you:

- Issue **API keys** (like GitHub/Stripe-style integration keys)
- Assign **scoped permissions** per key
- Protect DRF viewsets so only keys with the right permission can call each action
- Manage keys and permissions via **REST APIs** and Django admin

Typical flow:

1. Define permissions in code (`api_key_perm.py`)
2. Sync to database (`machine_auth_sync`)
3. Create API keys with selected permissions (management API or admin)
4. External systems call **your** viewsets with `Authorization: machine_auth <key>`

---

## 2) Requirements

- Python `>= 3.9`
- Django `>= 3.2`
- Django REST Framework `>= 3.13`

```bash
pip install django-machine-auth
```

---

## 3) Add app and settings

### Installed apps

```python
INSTALLED_APPS = [
    # ...
    "django_machine_auth",
]
```

### Machine auth settings

```python
MACHINE_AUTH = {
    "KEY_PREFIX": "mac_",                 # default: mac_
    "ENABLE_REQUEST_LOGGING": False,
    "LOGGING_MODE": "redacted",           # raw | redacted | metadata_only
    "CACHE_TIMEOUT": 3600,
}
```

### DRF throttle (required for protected APIs)

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "machine_api_key": "1000/hour",
    },
}
```

### Management API URLs (recommended)

Add once in project `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("machine-auth/", include("django_machine_auth.urls")),
]
```

This registers permission catalog and API key management routes under `/machine-auth/`.

---

## 4) Viewsets overview (read this first)

The library exposes **four viewsets**. Each solves a different problem.

| Viewset | Purpose | Do you inherit it? | Request authentication |
|---------|---------|--------------------|-------------------------|
| `MachineAuthViewSet` | Your **integration/business APIs** | **Yes** | `Authorization: machine_auth <key>` |
| `MachinePermissionViewSet` | **List assignable permissions** (UI dropdowns) | Optional (subclass to filter) | Your normal DRF auth (JWT, session, etc.) |
| `MachineAPIKeyManagementViewSet` | **Create/list/update/revoke keys** | Usually **no** (use package URLs) | Your normal DRF auth (JWT, session, etc.) |
| `MachineAPIKeyRequestLogViewSet` | **List/inspect request logs** for machine-auth traffic | Usually **no** (use package URLs) | Your normal DRF auth (JWT, session, etc.) |

Imports:

```python
from django_machine_auth.views import (
    MachineAuthViewSet,
    MachinePermissionViewSet,
    MachineAPIKeyManagementViewSet,
    MachineAPIKeyRequestLogViewSet,
)
```

### Three different “permission” concepts

| Name | Location | Role |
|------|----------|------|
| **Module definition** | `<app>/api_key_perm.py` | Permissions defined in code (source of truth) |
| **Permission registry** | `MachinePermission` model (DB) | Synced from code; used for validation and catalog API |
| **Key permissions** | `MachineAPIKey.permissions` (JSON list) | What a specific key is allowed to do at runtime |

---

## Part I — Define permissions in code

Permissions are **not** invented in the admin UI. They are defined in code, then synced to the database.

### Create `api_key_perm.py` in your Django app

Example: `complaint/api_key_perm.py`

```python
from django_machine_auth.decorators import api_key_module


@api_key_module("complaint", label="Complaint Management")
class ComplaintModule:
    crud = ["view", "create", "update", "delete"]
    actions = {
        "export": ["get"],
        "bulk_update": ["post"],
    }
```

This generates permissions such as:

- `complaint.view`, `complaint.create`, `complaint.update`, `complaint.delete`
- `complaint.export.get`
- `complaint.bulk_update.post`

Rules:

- The app must be in `INSTALLED_APPS`.
- If `api_key_perm.py` is missing, discovery skips that app (no error).
- Every custom action on your `MachineAuthViewSet` must appear under `actions` with the HTTP methods you use.

### Sync permissions to the database

```bash
python manage.py machine_auth_sync
python manage.py machine_auth_sync --dry-run   # preview changes
```

Run after every change to module definitions (deploy step).

### Print permission documentation

```bash
python manage.py machine_auth_permissions
```

---

## Part II — Protect your APIs (`MachineAuthViewSet`)

Use this viewset as the **base class for endpoints that integrations call with an API key**.

### What `MachineAuthViewSet` gives you

When you inherit it, DRF automatically uses:

- **Authentication:** `MachineAPIKeyAuthentication` (`Authorization: machine_auth <key>`)
- **Permission check:** `MachineAuthPermission` (compares key permissions to required permission)
- **Throttle:** `MachineAPIKeyRateThrottle` (scope `machine_api_key`)

You still add DRF mixins and your own logic (`get_queryset`, serializers, etc.).

### Minimal example

```python
from rest_framework import mixins
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class ComplaintMachineViewSet(MachineAuthViewSet, mixins.ListModelMixin):
    module = "complaint"  # REQUIRED — must match @api_key_module("complaint")

    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    # list/retrieve use complaint.view automatically
```

### Full example with custom action

```python
from rest_framework.decorators import action
from rest_framework.response import Response

from django_machine_auth.views import MachineAuthViewSet


class ComplaintMachineViewSet(MachineAuthViewSet, mixins.ListModelMixin):
    module = "complaint"

    def get_queryset(self):
        return Complaint.objects.filter_by_government(self.government)

    def list(self, request):
        qs = self.get_queryset()
        return Response(ComplaintSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def export(self, request):
        # Requires permission: complaint.export.get
        return Response({"status": "ok"})
```

`export` must be listed in `api_key_perm.py`:

```python
actions = {"export": ["get"]}
```

### Permission mapping (action → permission string)

| DRF `action` | HTTP | Required permission |
|--------------|------|-------------------|
| `list` | GET | `module.view` |
| `retrieve` | GET | `module.view` |
| `create` | POST | `module.create` |
| `update` | PUT | `module.update` |
| `partial_update` | PATCH | `module.update` |
| `destroy` | DELETE | `module.delete` |
| custom e.g. `export` | GET | `module.export.get` |
| custom e.g. `export` | POST | `module.export.post` |

### Register routes (your project URLs)

`MachineAuthViewSet` is **not** included in `django_machine_auth.urls`. You register it on **your** router:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from complaint.views import ComplaintMachineViewSet

router = DefaultRouter()
router.register("machine", ComplaintMachineViewSet, basename="complaint-machine")

urlpatterns = [
    path("v1/government/complaint/", include(router.urls)),
]
```

Integration URL example:

`GET /v1/government/complaint/machine/`

### Mixing with your existing base viewset (important)

If you also have a JWT/session base viewset, put **`MachineAuthViewSet` first** in the inheritance list:

```python
class ComplaintMachineViewSet(MachineAuthViewSet, BaseGovernmentViewSet, mixins.ListModelMixin):
    module = "complaint"
```

Otherwise `BaseGovernmentViewSet` may override `authentication_classes` and machine auth will not run.

Alternative: set explicitly on the combined class:

```python
class ComplaintMachineViewSet(BaseGovernmentViewSet, mixins.ListModelMixin):
    module = "complaint"
    authentication_classes = [MachineAPIKeyAuthentication]
    permission_classes = [MachineAuthPermission]
    throttle_classes = [MachineAPIKeyRateThrottle]
```

### Accessing the API key on the request

After successful authentication:

```python
def list(self, request):
    key = request.machine_api_key
    perms = key.permissions   # e.g. ["complaint.view", "complaint.export.get"]
    ...
```

### Startup validation

On Django startup, the package checks that:

- `module` on each `MachineAuthViewSet` is registered
- Custom actions exist in `api_key_perm.py` with correct HTTP methods

Fix errors by updating `api_key_perm.py` and running `machine_auth_sync`.

---

## Part III — Permission catalog API (`MachinePermissionViewSet`)

Use this when building a UI to **select permissions** before creating or updating an API key.

### Option A — Use built-in package route (easiest)

Already available if you added:

```python
path("machine-auth/", include("django_machine_auth.urls")),
```

Endpoints:

```http
GET /machine-auth/permissions/
GET /machine-auth/permissions/?module=complaint
GET /machine-auth/permissions/?search=export
```

Authentication: any **authenticated** user (your JWT/session).

Response fields: `id`, `module`, `permission`, `label`.

### Option B — Subclass to limit visible permissions (recommended for multi-tenant apps)

Override `get_queryset()` so users only see permissions they are allowed to assign:

```python
from django_machine_auth.views import MachinePermissionViewSet


class ComplaintPermissionViewSet(MachinePermissionViewSet):
    """Only complaint module permissions — for assignment UI."""

    def get_queryset(self):
        return super().get_queryset().filter(module="complaint")
```

Register on **your** router if you want a custom path:

```python
router.register("complaint-permissions", ComplaintPermissionViewSet, basename="complaint-permissions")
```

You can combine built-in query params **and** subclass filtering:

- Subclass limits module set
- `?search=` still works on the filtered queryset

### When to use catalog API vs code only

| Use catalog API | Use code + sync only |
|-----------------|----------------------|
| Frontend permission picker | Admin-only workflows |
| Self-service key creation with scoped choices | Fixed permission sets in backend |

---

## Part IV — API key management

Manage API keys via REST (create, list, inspect permissions, update, deactivate).

### Built-in routes (no subclass required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/machine-auth/machine-api-keys/` | List keys (scoped by user role) |
| POST | `/machine-auth/machine-api-keys/` | Create key; returns `raw_api_key` once |
| GET | `/machine-auth/machine-api-keys/{id}/` | Detail including **`permissions`** |
| PATCH | `/machine-auth/machine-api-keys/{id}/` | Update name, permissions, expiry, is_active |
| POST | `/machine-auth/machine-api-keys/{id}/deactivate/` | Revoke (`is_active=False`) |

Authentication: your DRF auth (JWT/session). User must be authenticated.

### Access rules

| Role | List | Create | Update / deactivate |
|------|------|--------|---------------------|
| **Superuser** | All keys (`?user=<id>` optional) | For self or **any** user | Any key |
| **Authenticated user** | Own keys only | **Self only** (`user` forced to request.user) | Own keys only |

### Create API key

```http
POST /machine-auth/machine-api-keys/
Authorization: Bearer <your_jwt>
Content-Type: application/json
```

```json
{
  "name": "Gov Portal Integration",
  "user": 5,
  "permissions": ["complaint.view", "complaint.export.get"],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

Response (store `raw_api_key` immediately — it is not shown again):

```json
{
  "id": 1,
  "name": "Gov Portal Integration",
  "user": 5,
  "permissions": ["complaint.view", "complaint.export.get"],
  "raw_api_key": "mac_xxxxxxxx",
  "is_active": true,
  "created_at": "..."
}
```

Non-superuser creating for another user → `400` on `user` field.

### List API keys

```http
GET /machine-auth/machine-api-keys/
```

Superuser optional filter:

```http
GET /machine-auth/machine-api-keys/?user=5
```

### Get permissions assigned to a key

```http
GET /machine-auth/machine-api-keys/1/
```

The `permissions` field is a list of strings, e.g. `["complaint.view", "complaint.export.get"]`.

### Update API key

```http
PATCH /machine-auth/machine-api-keys/1/
Content-Type: application/json

{"permissions": ["complaint.view"], "expires_at": "2027-01-01T00:00:00Z"}
```

### Deactivate (revoke)

```http
POST /machine-auth/machine-api-keys/1/deactivate/
```

Or `PATCH` with `"is_active": false`.

### Alternative: Django admin

You can still manage keys in Django admin (`MachineAPIKey`). Same validation rules apply.

### Advanced: subclass `MachineAPIKeyManagementViewSet`

Only if you need custom behavior (extra fields, auditing, different URL layout):

```python
from rest_framework.routers import DefaultRouter
from django_machine_auth.views import MachineAPIKeyManagementViewSet

router = DefaultRouter()
router.register("api-keys", MachineAPIKeyManagementViewSet, basename="api-keys")
```

Most projects should use `include("django_machine_auth.urls")` instead.

---

## Part V — Call protected APIs with an API key

This is **separate** from management APIs. Integrations call **your** `MachineAuthViewSet` routes.

### Header format

```text
Authorization: machine_auth <api_key>
```

Example:

```bash
curl -H "Authorization: machine_auth mac_xxxxxxxx" \
  http://localhost:8000/v1/government/complaint/machine/
```

### Typical responses

| Status | Meaning |
|--------|---------|
| `401` | Missing/invalid key, wrong prefix, expired, or inactive |
| `403` | Key valid but missing required permission for this action/method |
| `200` / `201` | Success |

### Checklist before calling

1. Key exists and `is_active=True`
2. Key not expired
3. Key `permissions` includes exact string (e.g. `complaint.view` for `list`)
4. Viewset `module` matches module in `api_key_perm.py`
5. Custom action declared in `actions` with correct methods

---

## Part VII — Request logs API (`MachineAPIKeyRequestLogViewSet`)

Browse audit logs written by `MachineAuthLoggingMiddleware` when integrations call your `MachineAuthViewSet` endpoints.

### Prerequisites

1. `ENABLE_REQUEST_LOGGING = True` in `MACHINE_AUTH`
2. `MachineAuthLoggingMiddleware` in `MIDDLEWARE` (see Part VI)
3. `path("machine-auth/", include("django_machine_auth.urls"))` in project `urls.py`

### Built-in routes (no subclass required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/machine-auth/request-logs/` | List logs (metadata on list) |
| GET | `/machine-auth/request-logs/{id}/` | Full log detail |

Read-only. Uses your DRF authentication (JWT/session), **not** `machine_auth`.

### Access rules

| Role | List | Retrieve | Filters |
|------|------|----------|---------|
| **Superuser** | All logs | Any log | `?user=<id>`, `?api_key=<id>` |
| **Authenticated user** | Logs for keys they own | Same scope | `?api_key=<id>` only for their keys; **403** if not |

### SuperAdmin examples

```http
GET /machine-auth/request-logs/
Authorization: Bearer <superuser_jwt>

GET /machine-auth/request-logs/?user=42
GET /machine-auth/request-logs/?api_key=7
```

### Regular user examples

```http
# All logs for all API keys you own
GET /machine-auth/request-logs/

# Logs for one of your keys
GET /machine-auth/request-logs/?api_key=7
```

If key `7` belongs to another user → **403 Forbidden**.

### List vs detail fields

| Endpoint | Fields |
|----------|--------|
| **List** | `id`, `api_key_id`, `api_key_name`, `user_id`, `url`, `method`, `status_code`, `duration`, `ip_address`, `created_at` |
| **Detail** | Above plus `headers`, `request_body`, `response_body` (content depends on `LOGGING_MODE`) |

### Security note

Use `LOGGING_MODE: "redacted"` or `"metadata_only"` in production. Detail responses may contain sensitive data when `raw` mode was used.

### Advanced: subclass

```python
from django_machine_auth.views import MachineAPIKeyRequestLogViewSet

class TenantRequestLogViewSet(MachineAPIKeyRequestLogViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(url__startswith="/tenant-a/")
```

---

## Part VI — Logging, commands, and troubleshooting

### Request logging (optional)

```python
MIDDLEWARE = [
    "django_machine_auth.middleware.logging_middleware.MachineAuthLoggingMiddleware",
]

MACHINE_AUTH = {
    "ENABLE_REQUEST_LOGGING": True,
    "LOGGING_MODE": "redacted",  # raw | redacted | metadata_only
}
```

Logs are written only when `request.machine_api_key` is set (successful machine auth on protected APIs).

### Commands

```bash
python manage.py machine_auth_sync
python manage.py machine_auth_permissions
```

### Common errors

**`No default throttle rate set for 'machine_api_key'`**

Add `machine_api_key` to `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`.

**`Module 'complaint' is not registered`**

Add/fix `api_key_perm.py` and run `machine_auth_sync`.

**`Action "export" not defined in module`**

Add to `actions` in `api_key_perm.py`.

**403 on valid key**

Permission string mismatch — use exact value from `GET /machine-auth/machine-api-keys/{id}/`.

**Management API works but logging empty**

Enable middleware + call a `MachineAuthViewSet` endpoint with a valid key (not only JWT management routes).

### Operational notes

- Rotate keys periodically
- Prefer `redacted` or `metadata_only` logging in production
- Run `machine_auth_sync` after permission code changes

See also: [docs/OPERATIONS.md](docs/OPERATIONS.md), [CHANGELOG.md](CHANGELOG.md), [UPGRADING.md](UPGRADING.md).

### Local development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/pytest -q
```

Example project: [examples/basic_project/](examples/basic_project/)
