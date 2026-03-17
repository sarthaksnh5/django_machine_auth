from django.core.cache import cache

from django_machine_auth.utils.settings import cache_timeout

CACHE_KEY_PREFIX = "machine_auth:key"


def build_cache_key(hashed_key: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{hashed_key}"


def get_cached_auth_payload(hashed_key: str):
    return cache.get(build_cache_key(hashed_key))


def set_cached_auth_payload(hashed_key: str, payload: dict):
    cache.set(build_cache_key(hashed_key), payload, cache_timeout())


def invalidate_auth_payload(hashed_key: str):
    cache.delete(build_cache_key(hashed_key))
