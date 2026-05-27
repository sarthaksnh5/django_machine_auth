# Release Checklist

## Pre-release

- Update version in `pyproject.toml` and `django_machine_auth/__init__.py`.
- Update `CHANGELOG.md` with release date and notable changes.
- Update user-facing docs: `README.md`, `setup.md`, and `UPGRADING.md` for new viewsets, URLs, or behavior changes.
- Run tests: `make test` (or `scripts/test.sh`).
- Run permission sync dry-run in a sample integration:
  - `python manage.py machine_auth_sync --dry-run`

## Build artifacts

- Build source and wheel distributions:
  - `python -m pip install build`
  - `python -m build`
- Verify artifacts:
  - `python -m pip install twine`
  - `python -m twine check dist/*`

## Smoke test built artifact

- Create clean virtualenv.
- Install wheel from `dist/`.
- Run import smoke:
  - `python -c "import django_machine_auth; print(django_machine_auth.__version__)"`

## Publish

- Tag release in VCS (`vX.Y.Z`).
- Publish to package index.
- Announce release notes and upgrade notes (`UPGRADING.md`).
