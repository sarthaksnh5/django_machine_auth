import hashlib
import hmac


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def compare_hashes(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)
