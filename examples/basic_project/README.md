# Basic Example Project

Minimal integration of `django_machine_auth` with DRF.

## What it demonstrates

- Module declaration in `demoapp/api_key_perm.py`
- Protected endpoint via `MachineAuthViewSet` (`GET /demo-users/`)
- Key-authenticated request using `Authorization: machine_auth <key>`

For management APIs (permissions catalog, key CRUD), add to your project `urls.py`:

```python
path("machine-auth/", include("django_machine_auth.urls")),
```

See the main [setup.md](../../setup.md) for full v0.2 documentation.

## Run

```bash
cd examples/basic_project
python manage.py migrate
python manage.py machine_auth_sync
python manage.py createsuperuser
python manage.py runserver
```

## Create a key

**Option A — Django admin:** Machine API Keys → Add.

**Option B — Management API** (after adding `machine-auth/` URLs and authenticating as a user):

```http
POST /machine-auth/machine-api-keys/
Authorization: Bearer <jwt-or-session>
Content-Type: application/json

{"name": "demo", "permissions": ["demo.view"]}
```

Store `raw_api_key` from the response; it is shown only once.

## Call the protected API

```bash
curl -H "Authorization: machine_auth mac_xxx" http://127.0.0.1:8000/demo-users/
```
