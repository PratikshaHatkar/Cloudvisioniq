import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from fastapi import Request, Header, HTTPException, status, Depends

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "visioniq-production-secure-jwt-secret-key-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # 7 days

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_password(password: str) -> tuple[bool, str]:
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt with salt.
    """
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash.
    """
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a signed JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a signed JWT access token.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

def extract_token_from_request(request: Request, authorization: Optional[str] = None) -> Optional[str]:
    """
    Extracts JWT from Authorization header, HttpOnly cookie, or query parameter.
    """
    # 1. Bearer header
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    # 2. HttpOnly Cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()

    # 3. Query Parameter (for authenticated evidence media / stream tags)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token.strip()

    return None

async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency validating the caller's JWT token and retrieving user profile.
    Raises 401 UNAUTHORIZED if missing, expired, or invalid.
    """
    token = extract_token_from_request(request, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]

    # Import storage lazily to prevent circular imports
    from src.api.storage import get_storage
    storage = get_storage()
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user.get("id") or user.get("user_id"),
        "user_id": user.get("id") or user.get("user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": user.get("created_at")
    }

async def get_optional_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional user dependency that returns None instead of raising 401 if unauthenticated.
    """
    try:
        return await get_current_user(request, authorization)
    except HTTPException:
        return None
