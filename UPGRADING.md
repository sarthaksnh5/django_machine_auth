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

If new settings are introduced, defaults are chosen to preserve prior behavior unless release notes specify otherwise.

## Deprecation Policy

- Deprecated behavior is announced in changelog and documentation before removal.
- Removals occur only in a major release unless critical security reasons require earlier action.
