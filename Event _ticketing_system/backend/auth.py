"""
Authentication and Authorization Module
Handles password hashing, JWT tokens, API Key authentication, and Role-Based Access Control (RBAC).
Integrates with MySQL database 'event_ticketing_db'.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import bcrypt
import jwt
from fastapi import Header, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pymysql

from backend.database import get_db, serialize_row

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "uptm_web_api_dev_secure_jwt_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a bcrypt hash."""
    try:
        # Standardize prefix for bcrypt compatibility ($2y$ to $2b$ if needed)
        h = hashed_password
        if h.startswith("$2y$"):
            h = "$2b$" + h[4:]
        return bcrypt.checkpw(plain_password.encode("utf-8"), h.encode("utf-8"))
    except Exception as e:
        print(f"[!] Password verification error: {e}")
        return False

def generate_api_key(prefix: str = "key") -> str:
    """Generates a secure cryptographically random API Key."""
    return f"{prefix}_{secrets.token_hex(16)}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JSON Web Token (JWT)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token_query: Optional[str] = Query(None, alias="token"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: pymysql.Connection = Depends(get_db)
) -> dict:
    """
    Authenticates the caller via either:
    1. HTTP Bearer JWT token in Authorization header
    2. JWT token in URL query parameter (?token=...)
    3. API Key in X-API-Key header
    """
    user = None

    # 1. Try Bearer Token or Query Parameter Token
    token = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif token_query:
        token = token_query.strip()

    if token:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject (user ID)."
            )
        cursor = db.cursor()
        cursor.execute(
            "SELECT user_id, full_name, email, role, phone, api_key, created_at FROM users WHERE user_id = %s",
            (int(user_id),)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token no longer exists."
            )
        user = serialize_row(row)

    # 2. Try API Key
    elif x_api_key:
        cursor = db.cursor()
        cursor.execute(
            "SELECT user_id, full_name, email, role, phone, api_key, created_at FROM users WHERE api_key = %s",
            (x_api_key.strip(),)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unauthorized API key provided."
            )
        user = serialize_row(row)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer JWT token or X-API-Key header."
        )

    return user

def require_roles(allowed_roles: List[str]):
    """Role-Based Access Control (RBAC) dependency factory."""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. This resource requires one of the following roles: {allowed_roles}. Your current role is '{user_role}'."
            )
        return current_user
    return role_checker
