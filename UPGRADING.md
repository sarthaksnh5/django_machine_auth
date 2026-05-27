# Upgrading Guide

This document explains how to safely upgrade `django_machine_auth` between releases.

## Versioning Contract

- The project follows Semantic Versioning.
- Breaking changes are introduced only in major versions.
- Minor and patch versions remain backward-compatible unless explicitly noted.

## Upgrade Checklist

1. Read `CHANGELOG.md` for the target version.
2. Upgrade package in a branch and run:
   - `python manage.py machine_auth_sync --dry-run`
   - your test suite
3. Apply DB migrations if present.
4. Run `python manage.py machine_auth_sync` in staging and production.
5. Verify machine-auth protected endpoints with a smoke test key.

## Configuration Compatibility

Review these settings after each upgrade:

- `MACHINE_AUTH.KEY_PREFIX`
- `MACHINE_AUTH.ENABLE_REQUEST_LOGGING`
- `MACHINE_AUTH.LOGGING_MODE`
- `MACHINE_AUTH.CACHE_TIMEOUT`
- `MACHINE_AUTH.STRICT_ACTION_VALIDATION` (default `False` since 0.3.1)

If new settings are introduced, defaults are chosen to preserve prior behavior unless release notes specify otherwise.

## Deprecation Policy

- Deprecated behavior is announced in changelog and documentation before removal.
- Removals occur only in a major release unless critical security reasons require earlier action.

## Upgrading to 0.2.0

### What changed

- **Management API expanded:** permission catalog and full API key lifecycle (list, retrieve, patch, deactivate).
- **Create keys:** no longer requires Django admin / `IsAdminUser`. Any authenticated user can create keys **for themselves**; superusers can create for any user.
- **Package URLs:** add `path("machine-auth/", include("django_machine_auth.urls"))` to expose:
  - `GET /machine-auth/permissions/`
  - CRUD-style routes under `/machine-auth/machine-api-keys/`

### Recommended steps

1. Upgrade the package: `pip install -U django-machine-auth>=0.2.0`
2. Add (or confirm) the URL include in your project `urls.py` (see [setup.md](setup.md#3-add-app-and-settings)).
3. Run migrations if you skipped any from 0.1.x: `python manage.py migrate`
4. Run `python manage.py machine_auth_sync`
5. Update any internal clients that assumed **admin-only** key creation to use JWT/session auth against `/machine-auth/machine-api-keys/`.
6. If you subclassed `MachineAPIKeyManagementViewSet` with custom `permission_classes = [IsAdminUser]`, review whether `CanManageMachineAPIKeys` (default on the viewset) meets your needs.

### Backward compatibility

- `MachineAuthViewSet`, authentication header format, and permission strings are unchanged.
- Existing API keys and `MachineAPIKey.permissions` JSON continue to work without migration of key data.
- Django admin key management remains available.

## Upgrading to 0.3.1

### What changed

- New setting `STRICT_ACTION_VALIDATION` (default **`False`**).
- Custom `@action`s **not** listed in `api_key_perm.py` no longer fail Django startup by default; a warning is logged instead.
- Those undeclared actions require only a **valid API key** at runtime (no scoped permission string).
- **CRUD** actions still always require permissions (`module.view`, `module.create`, etc.).

### Recommended for existing strict integrations

If you relied on startup failing when `@action` was missing from `api_key_perm.py`, set:

```python
MACHINE_AUTH = {
    "STRICT_ACTION_VALIDATION": True,
}
```

### Backward compatibility

- No migration required. Behavior change is configuration-driven.

## Upgrading to 0.3.0

### What changed

- New optional route: `GET /machine-auth/request-logs/` (and retrieve by id).
- Requires existing `APIKeyRequestLog` table (no new migration).
- Logging must still be enabled via middleware + `ENABLE_REQUEST_LOGGING` for new rows.

### Recommended steps

1. Upgrade: `pip install -U django-machine-auth>=0.3.0`
2. Confirm `path("machine-auth/", include("django_machine_auth.urls"))` is present (new route is included automatically).
3. Wire your SuperAdmin / user portal to the request-logs endpoints (JWT/session auth).

### Backward compatibility

- No breaking changes to existing viewsets or authentication.
