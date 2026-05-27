from django.conf import settings

DEFAULTS = {
    "KEY_PREFIX": "mac_",
    "ENABLE_REQUEST_LOGGING": False,
    "LOGGING_MODE": "redacted",
    "CACHE_TIMEOUT": 3600,
    "STRICT_ACTION_VALIDATION": False,
}


def get_machine_auth_setting(name):
    config = getattr(settings, "MACHINE_AUTH", {})
    return config.get(name, DEFAULTS[name])


def key_prefix():
    return get_machine_auth_setting("KEY_PREFIX") or DEFAULTS["KEY_PREFIX"]


def request_logging_enabled():
    return bool(get_machine_auth_setting("ENABLE_REQUEST_LOGGING"))


def logging_mode():
    mode = str(get_machine_auth_setting("LOGGING_MODE") or "redacted").lower()
    if mode not in {"raw", "redacted", "metadata_only"}:
        return "redacted"
    return mode


def cache_timeout():
    return int(get_machine_auth_setting("CACHE_TIMEOUT") or DEFAULTS["CACHE_TIMEOUT"])


def strict_action_validation():
    return bool(get_machine_auth_setting("STRICT_ACTION_VALIDATION"))
