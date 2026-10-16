"""
Users Resource Router
Provides complete CRUD endpoints for the /users resource.
Includes pagination, filtering, search, sorting, and RBAC protection.
Course: SWC3633 / SWC4443 Web API Development
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
import pymysql

from backend.database import get_db, serialize_row, serialize_rows
from backend.models import UserCreateAdmin, UserUpdate
from backend.auth import get_current_user, require_roles, hash_password, generate_api_key

router = APIRouter(prefix="/users", tags=["Users Resource"])

@router.get("", status_code=status.HTTP_200_OK)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[Literal["admin", "organiser", "customer"]] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search term for full_name or email"),
    sort_by: Literal["user_id", "full_name", "email", "role", "created_at"] = Query("created_at", description="Field to sort by"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Retrieves a paginated list of users who signed up with filtering, search, and activity metrics."""
    cursor = db.cursor()
    conditions = []
    params = []

    if role:
        conditions.append("role = %s")
        params.append(role)

    if search:
        conditions.append("(full_name LIKE %s OR email LIKE %s OR phone LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Total count query
    count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
    cursor.execute(count_sql, params)
    total_items = cursor.fetchone()["total"]

    # Paginated select query with live booking metrics
    offset = (page - 1) * limit
    order_clause = f"ORDER BY {sort_by} {order.upper()}"
    select_sql = f"""
        SELECT 
            user_id, full_name, email, role, api_key, phone, last_login_at, created_at,
            (SELECT COUNT(*) FROM bookings b WHERE b.user_id = users.user_id) as total_bookings,
            (SELECT COALESCE(SUM(b.total_amount), 0) FROM bookings b WHERE b.user_id = users.user_id AND b.booking_status != 'cancelled') as total_spent,
            TIMESTAMPDIFF(MINUTE, created_at, NOW()) as signed_up_minutes_ago
        FROM users
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_sql, params + [limit, offset])
    rows = cursor.fetchall()
    users = serialize_rows(rows)

    total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

    return {
        "status": "success",
        "data": users,
        "pagination": {
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/logins", status_code=status.HTTP_200_OK)
def get_user_login_history(
    limit: int = Query(50, ge=1, le=200, description="Number of recent logins to retrieve"),
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Retrieves the live audit trail of users who signed into the system."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            l.login_id, l.user_id, l.ip_address, l.user_agent, l.login_time,
            u.full_name, u.email, u.role, u.last_login_at,
            TIMESTAMPDIFF(MINUTE, l.login_time, NOW()) as minutes_ago
        FROM user_logins l
        JOIN users u ON l.user_id = u.user_id
        ORDER BY l.login_time DESC
        LIMIT %s
    """, (limit,))
    logins = serialize_rows(cursor.fetchall())
    return {
        "status": "success",
        "data": logins,
        "total": len(logins)
    }

@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """Retrieves a specific user profile by ID. Allowed for Admin or the user themselves."""
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only view your own user profile."
        )

    cursor = db.cursor()
    cursor.execute("SELECT user_id, full_name, email, role, api_key, phone, created_at FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    return {
        "status": "success",
        "data": serialize_row(row)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user_admin(
    payload: UserCreateAdmin,
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Creates a new user with designated role and generates an API key."""
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (payload.email.lower(),))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    hashed_pw = hash_password(payload.password)
    api_prefix = "adm" if payload.role == "admin" else "org" if payload.role == "organiser" else "cus"
    api_key = generate_api_key(api_prefix)

    cursor.execute("""
        INSERT INTO users (full_name, email, password_hash, role, api_key, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (payload.full_name.strip(), payload.email.lower(), hashed_pw, payload.role, api_key, payload.phone))

    new_id = cursor.lastrowid
    cursor.execute("SELECT user_id, full_name, email, role, api_key, phone, created_at FROM users WHERE user_id = %s", (new_id,))
    created_user = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": f"User '{payload.full_name}' created successfully with role '{payload.role}'.",
        "data": created_user
    }

@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """Updates user information. Regular users can edit own profile; Admins can edit any user and role."""
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only edit your own account.")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    updates = []
    params = []

    if payload.full_name is not None:
        updates.append("full_name = %s")
        params.append(payload.full_name.strip())

    if payload.phone is not None:
        updates.append("phone = %s")
        params.append(payload.phone.strip())

    if payload.password is not None:
        updates.append("password_hash = %s")
        params.append(hash_password(payload.password))

    if payload.role is not None:
        if current_user["role"] != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can modify user roles.")
        updates.append("role = %s")
        params.append(payload.role)

    if updates:
        params.append(user_id)
        update_sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
        cursor.execute(update_sql, params)

    cursor.execute("SELECT user_id, full_name, email, role, api_key, phone, created_at FROM users WHERE user_id = %s", (user_id,))
    updated_user = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": "User updated successfully.",
        "data": updated_user
    }

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Deletes a user account."""
    if current_user["user_id"] == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account.")

    cursor = db.cursor()
    cursor.execute("SELECT user_id, full_name FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    return {
        "status": "success",
        "message": f"User '{user['full_name']}' (ID: {user_id}) deleted successfully."
    }
