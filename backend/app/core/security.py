from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set, Union
import bcrypt
import jwt
from pydantic import BaseModel
from app.core.config import settings


# In-memory revocation set for logged-out / refreshed tokens
_REVOKED_TOKENS: Set[str] = set()


class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str  # "teacher" | "student" | "parent" | "admin"
    school_id: str
    type: str = "access"  # "access" | "refresh"
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    role: str,
    school_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates an access token valid for 15 minutes by default.
    JWT carries: user id (sub), role, school_id, type="access".
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "role": role,
        "school_id": school_id,
        "type": "access",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    role: str,
    school_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a refresh token valid for 7 days by default.
    JWT carries: user id (sub), role, school_id, type="refresh".
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "role": role,
        "school_id": school_id,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def revoke_token(token: str) -> None:
    """Add a token to the revoked set upon logout."""
    _REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    """Check if token has been revoked."""
    return token in _REVOKED_TOKENS


def decode_access_token(token: str, expected_type: Optional[str] = "access") -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access or refresh token.
    Verifies signature, expiration, revocation status, and expected type.
    """
    if is_token_revoked(token):
        return None
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        # If expected_type is specified, verify token type match
        if expected_type is not None:
            token_type = decoded.get("type")
            # For backward compatibility, default to "access" if type not present
            if token_type and token_type != expected_type:
                return None
            if not token_type and expected_type != "access":
                return None
        return decoded
    except jwt.PyJWTError:
        return None
