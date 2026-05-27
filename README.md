# django_machine_auth

[![PyPI](https://img.shields.io/pypi/v/django-machine-auth)](https://pypi.org/project/django-machine-auth/)

API key authentication for Django REST Framework with module-scoped permissions (similar to how platforms like GitHub, Stripe, or OpenAI expose scoped API keys).

**Current version:** 0.3.1 — relaxed custom-action validation (opt-in strict mode).

## Documentation map

| Guide | Audience |
|-------|----------|
| [setup.md](setup.md) | Full step-by-step setup (recommended for first integration) |
| This README | Quick reference and viewset overview |

### Topics in setup.md

1. [Installation and settings](setup.md#2-requirements)
2. [Part I — Define permissions in code](setup.md#part-i--define-permissions-in-code)
3. [Part II — Protect your APIs (`MachineAuthViewSet`)](setup.md#part-ii--protect-your-apis-machineauthviewset)
4. [Part III — Permission catalog API (`MachinePermissionViewSet`)](setup.md#part-iii--permission-catalog-api-machinepermissionviewset)
5. [Part IV — API key management](setup.md#part-iv--api-key-management)
6. [Part V — Call protected APIs with an API key](setup.md#part-v--call-protected-apis-with-an-api-key)
7. [Part VII — Request logs API](setup.md#part-vii--request-logs-api-machineapikeyrequestlogviewset)
8. [Logging, commands, troubleshooting](setup.md#part-vi--logging-commands-and-troubleshooting)

---

## Viewsets at a glance

The package provides **four viewsets** for four different jobs. Do not mix them up.

| Viewset | When to use | Inherit in your project? | Auth on requests |
|---------|-------------|---------------------------|------------------|
| `MachineAuthViewSet` | Protect **your business APIs** (integrations call these) | **Yes** | `Authorization: machine_auth <key>` |
| `MachinePermissionViewSet` | List permissions for **assignment UI** (dropdowns) | **Optional** (subclass to filter) | JWT / session (your DRF auth) |
| `MachineAPIKeyManagementViewSet` | Create/list/update/revoke keys | **Usually no** (use package URLs) | JWT / session (your DRF auth) |
| `MachineAPIKeyRequestLogViewSet` | List/inspect machine-auth **request logs** | **Usually no** (use package URLs) | JWT / session (your DRF auth) |

Import from:

```python
from django_machine_auth.views import (
    MachineAuthViewSet,
    MachinePermissionViewSet,
    MachineAPIKeyManagementViewSet,
    MachineAPIKeyRequestLogViewSet,
)
```

---

## Quick start

### 1. Install and configure

```bash
pip install django-machine-auth
```

```python
INSTALLED_APPS = ["django_machine_auth", ...]

MACHINE_AUTH = {
    "KEY_PREFIX": "mac_",
    "ENABLE_REQUEST_LOGGING": False,
    "LOGGING_MODE": "redacted",
    "CACHE_TIMEOUT": 3600,
    "STRICT_ACTION_VALIDATION": False,  # True = require all @actions in api_key_perm.py
}

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "machine_api_key": "1000/hour",
    },
}
```

### 2. Wire management URLs (one line)

```python
path("machine-auth/", include("django_machine_auth.urls")),
```

### 3. Define permissions in code

`your_app/api_key_perm.py`:

```python
from django_machine_auth.decorators import api_key_module


@api_key_module("complaint", label="Complaint")
class ComplaintModule:
    crud = ["view", "create", "update", "delete"]
    actions = {"export": ["get"]}
```

Then:

```bash
python manage.py machine_auth_sync
```

### 4. Protect your API — inherit `MachineAuthViewSet`

```python
from rest_framework import mixins
from rest_framework.response import Response
from django_machine_auth.views import MachineAuthViewSet


class ComplaintMachineViewSet(MachineAuthViewSet, mixins.ListModelMixin):
    module = "complaint"  # required — must match api_key_perm.py

    def get_queryset(self):
        return Complaint.objects.filter(...)

    def list(self, request):
        return Response(ComplaintSerializer(self.get_queryset(), many=True).data)
```

Register on **your** router (e.g. `/v1/complaint/machine/`).

### 5. Create keys and call your API

Management (JWT/session):

```http
POST /machine-auth/machine-api-keys/
```

Integration call:

```http
GET /v1/complaint/machine/
Authorization: machine_auth mac_xxxxx
```

---

## `MachineAuthViewSet` (protect your APIs)

**Purpose:** Endpoints that external systems call using an API key.

**What it provides automatically:**

- `MachineAPIKeyAuthentication`
- `MachineAuthPermission` (checks key’s permission list vs action + HTTP method)
- `MachineAPIKeyRateThrottle`

**You must:**

1. Set `module = "<name>"` matching `@api_key_module("<name>")`.
2. Add DRF mixins (`ListModelMixin`, etc.) and implement actions.
3. Declare custom `@action` names in `api_key_perm.py` under `actions` (required when `STRICT_ACTION_VALIDATION` is `True`; optional otherwise).
4. If mixing with another base viewset (e.g. JWT), put `MachineAuthViewSet` **first** in inheritance, or set `authentication_classes` / `permission_classes` explicitly on the combined class.

**Custom actions not in `api_key_perm.py`:** With default `STRICT_ACTION_VALIDATION: False`, undeclared `@action`s only require a valid API key (no scoped permission). Set `STRICT_ACTION_VALIDATION: True` for strict catalog + permission checks on every custom action.

**Permission mapping:**

| DRF action | Required permission |
|------------|---------------------|
| `list`, `retrieve` | `module.view` |
| `create` | `module.create` |
| `update`, `partial_update` | `module.update` |
| `destroy` | `module.delete` |
| custom `@action` | `module.<action>.<method_lower>` |

**After auth:** `request.machine_api_key` is set; use `request.machine_api_key.permissions` if needed.

Details: [setup.md — Part II](setup.md#part-ii--protect-your-apis-machineauthviewset).

---

## `MachinePermissionViewSet` (permission catalog)

**Purpose:** Return assignable permissions from the database (for UI when creating/updating keys).

**Default route (no subclass needed):**

- `GET /machine-auth/permissions/`
- `GET /machine-auth/permissions/?module=complaint`
- `GET /machine-auth/permissions/?search=export`

**Restrict what users can assign** — subclass and override `get_queryset()`:

```python
from django_machine_auth.views import MachinePermissionViewSet


class ComplaintPermissionViewSet(MachinePermissionViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(module="complaint")
```

Register the subclass on your router only if you need a custom path; otherwise use built-in filters.

Details: [setup.md — Part III](setup.md#part-iii--permission-catalog-api-machinepermissionviewset).

---

## API key management

**Purpose:** Create, list, inspect, update, and revoke API keys (admin portal / internal API).

**Use package URLs** (recommended):

| Method | Path |
|--------|------|
| GET | `/machine-auth/permissions/` |
| GET | `/machine-auth/machine-api-keys/` |
| POST | `/machine-auth/machine-api-keys/` |
| GET | `/machine-auth/machine-api-keys/{id}/` |
| PATCH | `/machine-auth/machine-api-keys/{id}/` |
| POST | `/machine-auth/machine-api-keys/{id}/deactivate/` |

**Access:**

- Superuser: all keys; create for any user; list filter `?user=<id>`.
- Authenticated user: own keys only; create only for self.

`raw_api_key` is returned **once** on create. List/retrieve never expose `hashed_key`.

Details: [setup.md — Part IV](setup.md#part-iv--api-key-management).

---

## Request logs API

**Purpose:** Browse audit logs for machine-authenticated API calls (SuperAdmin portal or user self-service).

**Prerequisites:** `ENABLE_REQUEST_LOGGING = True` and `MachineAuthLoggingMiddleware` installed.

| Method | Path |
|--------|------|
| GET | `/machine-auth/request-logs/` |
| GET | `/machine-auth/request-logs/{id}/` |

**Access:**

- **Superuser:** all logs; `?user=<id>`, `?api_key=<id>`.
- **Authenticated user:** logs for API keys they own; `?api_key=<id>` (403 if not their key).

**List** returns metadata only (method, url, status, duration, etc.). **Detail** includes `headers`, `request_body`, `response_body` when stored.

Details: [setup.md — Part VII](setup.md#part-vii--request-logs-api-machineapikeyrequestlogviewset).

---

## Three “permission” concepts (do not confuse)

| Concept | Where it lives | Used for |
|---------|----------------|----------|
| Module definition | `api_key_perm.py` in your app | Source of truth in code |
| Permission registry | `MachinePermission` table | Validation + catalog API |
| Key permissions | `MachineAPIKey.permissions` JSON | Runtime checks on protected APIs |

Flow: **code** → `machine_auth_sync` → **DB** → assign on key → **MachineAuthViewSet** enforces on each request.

---

## Logging

```python
MIDDLEWARE = [
    "django_machine_auth.middleware.logging_middleware.MachineAuthLoggingMiddleware",
]
MACHINE_AUTH = {"ENABLE_REQUEST_LOGGING": True, "LOGGING_MODE": "redacted"}
```

Only requests with successful machine auth context are logged.

---

## Management commands

```bash
python manage.py machine_auth_sync          # DB ← code permissions
python manage.py machine_auth_permissions   # print permission docs
```

---

## Troubleshooting

- **403 on protected API:** key missing exact permission string (e.g. `complaint.export.get`).
- **401:** invalid/expired/inactive key or wrong `KEY_PREFIX`.
- **Module not registered:** `view.module` must match `api_key_perm.py`; run sync.
- **Throttle error:** set `machine_api_key` in `DEFAULT_THROTTLE_RATES`.
- **Logging empty:** middleware enabled + valid machine auth on request.
- **Log API 403 on `?api_key=`:** key belongs to another user.
- **Startup error for undeclared `@action`:** set `STRICT_ACTION_VALIDATION: False` (default) or add the action to `api_key_perm.py`.

---

## More

- [CHANGELOG.md](CHANGELOG.md)
- [UPGRADING.md](UPGRADING.md)
- [docs/OPERATIONS.md](docs/OPERATIONS.md)
