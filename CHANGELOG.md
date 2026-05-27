# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog and this project follows Semantic Versioning.

## [0.3.1] - 2026-05-27

### Added
- `MACHINE_AUTH["STRICT_ACTION_VALIDATION"]` (default `False`): relaxed mode for custom `@action`s not listed in `api_key_perm.py`.
- When relaxed: startup logs warnings instead of raising; runtime skips permission check for undeclared custom actions (API key auth still required).
- CRUD actions (`list`, `create`, etc.) always require permissions regardless of this setting.

### Changed
- Default behavior is now relaxed for custom actions. Set `STRICT_ACTION_VALIDATION: True` to restore pre-0.3.1 strict startup errors and permission checks on all custom actions.

## [0.3.0] - 2026-05-27

### Added
- `MachineAPIKeyRequestLogViewSet` — read-only request log API at `GET /machine-auth/request-logs/`.
- `CanViewMachineAPIKeyLogs` permission class (superuser: all logs; users: logs for keys they own).
- Superuser filters: `?user=<id>`, `?api_key=<id>`.
- List serializer returns metadata only; detail includes headers and bodies (per `LOGGING_MODE`).
- Regular user `?api_key=<id>` returns 403 if the key is not theirs.

## [0.2.0] - 2026-03-17

### Added
- `MachinePermissionViewSet` for DB-backed permission catalog (`GET /machine-auth/permissions/`).
- Built-in permission filters: `?module=` and `?search=`.
- Expanded `MachineAPIKeyManagementViewSet`:
  - list, retrieve, partial update, deactivate
  - superuser can manage all keys; users manage own keys only
  - superuser can create keys for any user; users create keys for self only
- `CanManageMachineAPIKeys` permission class for scoped key management.
- List/detail/update serializers for API keys (permissions visible on retrieve/list; secrets never exposed).

### Changed
- API key create is no longer admin-only; authenticated users can create keys for themselves.
- Package URLs now register both `permissions` and `machine-api-keys` routes.

## [0.1.0] - 2026-03-16

### Added
- Initial `django_machine_auth` package scaffold.
- Machine API key authentication with SHA256 hash verification.
- Module registry and decorator-driven permission generation.
- DRF permission class, throttle class, and base machine viewset.
- DB models for API keys, permission registry, and request logs.
- Request logging middleware with `raw`, `redacted`, and `metadata_only` modes.
- Admin UI for key generation and permission assignment.
- Management commands: `machine_auth_sync`, `machine_auth_permissions`.
- Startup validation for module registration and custom action declarations.
- Test suite for auth, command behavior, middleware logging, admin validation, and cache invalidation.

## Release Notes Policy

- `MAJOR`: breaking API/configuration changes.
- `MINOR`: backward-compatible features and enhancements.
- `PATCH`: backward-compatible bug fixes only.

## Unreleased Template

```markdown
## [x.y.z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Deprecated
- ...

### Removed
- ...
```
