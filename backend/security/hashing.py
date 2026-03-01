import secrets
import string

import bcrypt


def hash_api_key(raw_key: str) -> str:
    return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_api_key(raw_key: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw_key.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def generate_api_key() -> tuple[str, str, str]:
    alphabet = string.ascii_lowercase + string.digits
    prefix = "dev_" + "".join(secrets.choice(alphabet) for _ in range(6))
    secret = secrets.token_urlsafe(32)
    raw_key = f"{prefix}.{secret}"
    hashed = hash_api_key(raw_key)
    return prefix, raw_key, hashed
