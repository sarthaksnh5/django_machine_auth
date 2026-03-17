from django_machine_auth.utils.hashing import hash_api_key
from django_machine_auth.utils.key_generator import generate_api_key


def test_generate_api_key_has_prefix(settings):
    settings.MACHINE_AUTH = {"KEY_PREFIX": "mac_"}
    raw = generate_api_key()
    assert raw.startswith("mac_")


def test_hash_api_key_is_sha256_hex():
    value = hash_api_key("mac_test")
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)
