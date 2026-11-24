import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "markscan-api"

if len(JWT_SECRET_KEY) < 32 or JWT_SECRET_KEY == "replace_with_a_long_random_secret":
    raise RuntimeError(
        "JWT_SECRET_KEY must be set to a unique random value of at least 32 characters."
    )


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password_and_upgrade(password: str, stored_password: str) -> tuple[bool, str | None]:
    """Verify an Argon2 hash; transparently upgrade a legacy plaintext DB value."""
    if not stored_password:
        return False, None

    if stored_password.startswith("$argon2"):
        try:
            valid = _password_hasher.verify(stored_password, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False, None
        replacement = (
            hash_password(password)
            if _password_hasher.check_needs_rehash(stored_password)
            else None
        )
        return valid, replacement

    # Temporary migration path for existing accounts. Successful login replaces
    # the plaintext value with an Argon2id hash. Exposed passwords must still be reset.
    import hmac

    if hmac.compare_digest(password, stored_password):
        return True, hash_password(password)
    return False, None


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.lower(),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
