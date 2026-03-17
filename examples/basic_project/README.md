# Basic Example Project

This example shows minimal integration of `django_machine_auth` with DRF.

## What it demonstrates

- module declaration in `demoapp/api_key_perm.py`
- protected endpoint via `MachineAuthViewSet`
- key-authenticated request using `Authorization: machine_auth <key>`

## Run (example flow)

```bash
python manage.py migrate
python manage.py machine_auth_sync
python manage.py createsuperuser
python manage.py runserver
```

Then create a machine key in admin and call:

```bash
curl -H "Authorization: machine_auth mac_xxx" http://127.0.0.1:8000/demo-users/
```
