import secrets

from django_machine_auth.utils.settings import key_prefix


def generate_api_key(prefix: str = None) -> str:
    effective_prefix = prefix or key_prefix()
    return f"{effective_prefix}{secrets.token_urlsafe(32)}"
