# Migration Compatibility Notes

## Current baseline

- Initial schema starts at `django_machine_auth/migrations/0001_initial.py`.
- Core models:
  - `MachineAPIKey`
  - `MachinePermission`
  - `APIKeyRequestLog`

## Forward-compatibility rules

- Additive changes should prefer nullable or defaulted fields.
- Avoid destructive schema changes in minor/patch versions.
- When renaming/removing columns, provide a deprecation window and data migration path.

## Deployment guidance

1. Apply migrations in maintenance-safe deploy sequence.
2. Run `python manage.py machine_auth_sync` after deploy.
3. Validate admin key operations and a machine-authenticated endpoint.

## Data migration safeguards

- Preserve `hashed_key` integrity and uniqueness.
- Preserve existing `permissions` JSON values unless explicitly migrated.
- Never attempt to reconstruct raw API keys from stored hashes.
