from django_machine_auth.registry.module_registry import discover_modules


def test_discover_modules_ignores_apps_without_api_key_perm():
    # If this raises, discovery incorrectly fails on missing app.api_key_perm modules.
    discover_modules()
