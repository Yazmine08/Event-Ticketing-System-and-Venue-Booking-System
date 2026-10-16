"""
Authentication Endpoints
Handles user registration, login, profile retrieval, and API Key regeneration.
Course: SWC3633 / SWC4443 Web API Development
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
import pymysql

from backend.database import get_db, serialize_row
from backend.models import UserRegister, UserLogin
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_api_key,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, request: Request = None, db: pymysql.Connection = Depends(get_db)):
    """Registers a new customer or organiser account and records the initial sign-in audit."""
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (payload.email.lower(),))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists."
        )

    hashed_pw = hash_password(payload.password)
    api_prefix = "org" if payload.role == "organiser" else "cus"
    api_key = generate_api_key(api_prefix)
    user_name = payload.display_name

    cursor.execute("""
        INSERT INTO users (full_name, email, password_hash, role, api_key, phone, last_login_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (user_name, payload.email.lower(), hashed_pw, payload.role, api_key, payload.phone))

    user_id = cursor.lastrowid

    # Record initial login audit event
    try:
        ip = request.client.host if request and request.client else "127.0.0.1"
        raw_agent = request.headers.get("user-agent", "Browser Client") if request else "Browser Client"
        user_agent = raw_agent[:250]
        cursor.execute(
            "INSERT INTO user_logins (user_id, ip_address, user_agent, login_time) VALUES (%s, %s, %s, NOW())",
            (user_id, ip, user_agent)
        )
    except Exception as track_err:
        print(f"[!] Register login tracking error: {track_err}")

    token = create_access_token(data={"sub": str(user_id), "role": payload.role, "email": payload.email.lower()})

    return {
        "status": "success",
        "message": "User registered successfully.",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "full_name": user_name,
                "email": payload.email.lower(),
                "role": payload.role,
                "api_key": api_key,
                "phone": payload.phone,
                "last_login_at": "Just now"
            }
        }
    }

@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(payload: UserLogin, request: Request, db: pymysql.Connection = Depends(get_db)):
    """Logs in an administrator, organiser, or customer and records sign-in audit history."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (payload.email.lower(),))
    user_row = cursor.fetchone()

    if not user_row or not verify_password(payload.password, user_row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    # Record login telemetry and update user's last_login_at
    try:
        ip = request.client.host if request and request.client else "127.0.0.1"
        raw_agent = request.headers.get("user-agent", "Browser Client") if request else "Browser Client"
        user_agent = raw_agent[:250]
        cursor.execute("UPDATE users SET last_login_at = NOW() WHERE user_id = %s", (user_row["user_id"],))
        cursor.execute(
            "INSERT INTO user_logins (user_id, ip_address, user_agent, login_time) VALUES (%s, %s, %s, NOW())",
            (user_row["user_id"], ip, user_agent)
        )
    except Exception as track_err:
        print(f"[!] Login tracking error: {track_err}")

    user = serialize_row(user_row)
    token = create_access_token(data={"sub": str(user["user_id"]), "role": user["role"], "email": user["email"]})

    return {
        "status": "success",
        "message": "Login successful.",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "api_key": user.get("api_key"),
                "phone": user.get("phone"),
                "last_login_at": user.get("last_login_at")
            }
        }
    }

@router.get("/me", status_code=status.HTTP_200_OK)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile and active API key."""
    return {
        "status": "success",
        "data": current_user
    }
