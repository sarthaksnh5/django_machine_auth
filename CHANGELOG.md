# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog and this project follows Semantic Versioning.

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
