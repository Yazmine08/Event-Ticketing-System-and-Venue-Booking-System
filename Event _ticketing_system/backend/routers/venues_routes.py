"""
Venues Resource Router
Provides complete CRUD endpoints for the /venues resource.
Includes pagination, filtering, search, sorting, and RBAC protection.
Course: SWC3633 / SWC4443 Web API Development
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
import pymysql

from backend.database import get_db, serialize_row, serialize_rows
from backend.models import VenueCreate, VenueUpdate
from backend.auth import get_current_user, require_roles

router = APIRouter(prefix="/venues", tags=["Venues Resource"])

@router.get("", status_code=status.HTTP_200_OK)
def list_venues(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    approval_status: Optional[str] = Query(None, description="Filter by approval status: pending, approved, rejected"),
    search: Optional[str] = Query(None, description="Search venue name or location"),
    sort_by: Literal["venue_id", "venue_name", "location", "capacity", "approval_status"] = Query("venue_id"),
    order: Literal["asc", "desc"] = Query("asc"),
    db: pymysql.Connection = Depends(get_db)
):
    """Retrieves all venues with pagination, status filtering, search, and sorting."""
    cursor = db.cursor()
    conditions = []
    params = []

    if approval_status:
        conditions.append("approval_status = %s")
        params.append(approval_status)

    if search:
        conditions.append("(venue_name LIKE %s OR location LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count
    cursor.execute(f"SELECT COUNT(*) as total FROM venues {where_clause}", params)
    total_items = cursor.fetchone()["total"]

    # Select
    offset = (page - 1) * limit
    order_clause = f"ORDER BY {sort_by} {order.upper()}"
    select_sql = f"""
        SELECT venue_id, venue_name, location, capacity, description, approval_status
        FROM venues
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_sql, params + [limit, offset])
    venues = serialize_rows(cursor.fetchall())

    total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

    return {
        "status": "success",
        "data": venues,
        "pagination": {
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{venue_id}", status_code=status.HTTP_200_OK)
def get_venue_by_id(venue_id: int, db: pymysql.Connection = Depends(get_db)):
    """Retrieves a specific venue by ID."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM venues WHERE venue_id = %s", (venue_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venue with ID {venue_id} not found.")

    return {
        "status": "success",
        "data": serialize_row(row)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_venue(
    payload: VenueCreate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Creates a new venue. Auto-approved for admins; pending for organisers."""
    cursor = db.cursor()
    status_val = payload.approval_status or ("approved" if current_user["role"] == "admin" else "pending")
    venue_name = payload.resolved_name
    location = payload.resolved_location

    cursor.execute("""
        INSERT INTO venues (venue_name, location, capacity, description, approval_status)
        VALUES (%s, %s, %s, %s, %s)
    """, (venue_name, location, payload.capacity, payload.description, status_val))

    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM venues WHERE venue_id = %s", (new_id,))
    created_venue = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": f"Venue '{venue_name}' created successfully with status '{status_val}'.",
        "data": created_venue
    }

@router.put("/{venue_id}", status_code=status.HTTP_200_OK)
def update_venue(
    venue_id: int,
    payload: VenueUpdate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Updates venue details. Only Admins can modify approval_status."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM venues WHERE venue_id = %s", (venue_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venue with ID {venue_id} not found.")

    updates = []
    params = []

    if payload.venue_name is not None:
        updates.append("venue_name = %s")
        params.append(payload.venue_name.strip())

    if payload.location is not None:
        updates.append("location = %s")
        params.append(payload.location.strip())

    if payload.capacity is not None:
        updates.append("capacity = %s")
        params.append(payload.capacity)

    if payload.description is not None:
        updates.append("description = %s")
        params.append(payload.description)

    if payload.approval_status is not None:
        if current_user["role"] != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can approve or reject venues.")
        updates.append("approval_status = %s")
        params.append(payload.approval_status)

    if updates:
        params.append(venue_id)
        update_sql = f"UPDATE venues SET {', '.join(updates)} WHERE venue_id = %s"
        cursor.execute(update_sql, params)

    cursor.execute("SELECT * FROM venues WHERE venue_id = %s", (venue_id,))
    updated_venue = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": "Venue updated successfully.",
        "data": updated_venue
    }

@router.delete("/{venue_id}", status_code=status.HTTP_200_OK)
def delete_venue(
    venue_id: int,
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Deletes a venue if it has no associated active events."""
    cursor = db.cursor()
    cursor.execute("SELECT venue_id, venue_name FROM venues WHERE venue_id = %s", (venue_id,))
    venue = cursor.fetchone()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venue with ID {venue_id} not found.")

    # Check if events reference this venue
    cursor.execute("SELECT COUNT(*) as event_count FROM events WHERE venue_id = %s", (venue_id,))
    event_count = cursor.fetchone()["event_count"]
    if event_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete venue '{venue['venue_name']}' because it is linked to {event_count} active event(s)."
        )

    cursor.execute("DELETE FROM venues WHERE venue_id = %s", (venue_id,))
    return {
        "status": "success",
        "message": f"Venue '{venue['venue_name']}' (ID: {venue_id}) deleted successfully."
    }
