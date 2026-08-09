"""
Password hashing + JWT creation/verification.

Mirrors:
- djangorestframework_simplejwt token creation (access/refresh, custom claims)
- the custom password-complexity checks from the old
  accounts/serializers.py -> SignupRequestSerializer.validate()
"""
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password_complexity(password: str) -> list[str]:
    """Replicates the old serializer's password checks."""
    errors: list[str] = []

    if len(password) < 8:
        errors.append("This password is too short. It must contain at least 8 characters.")

    if password.isdigit():
        errors.append("This password is entirely numeric.")

    pattern_checks = [
        (r".*[A-Z].*", "Password must contain at least 1 uppercase letter."),
        (r".*[a-z].*", "Password must contain at least 1 lowercase letter."),
        (r".*\d.*", "Password must contain at least 1 number."),
        (r".*[\W_].*", "Password must contain at least 1 special character."),
    ]
    for pattern, message in pattern_checks:
        if not re.search(pattern, password):
            errors.append(message)

    return errors


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": uuid.uuid4().hex,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token(user_id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES), "refresh")


def decode_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError (or subclasses) if invalid/expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])