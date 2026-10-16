"""
Events Resource Router
Provides complete CRUD endpoints for the /events resource.
Includes pagination, filtering, search, sorting, and role authorization.
Course: SWC3633 / SWC4443 Web API Development
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
import pymysql

from backend.database import get_db, serialize_row, serialize_rows
from backend.models import EventCreate, EventUpdate
from backend.auth import get_current_user, require_roles

router = APIRouter(prefix="/events", tags=["Events Resource"])

@router.get("", status_code=status.HTTP_200_OK)
def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    venue_id: Optional[int] = Query(None, description="Filter by venue ID"),
    organiser_id: Optional[int] = Query(None, description="Filter by organiser user ID"),
    status: Optional[str] = Query(None, description="Filter by event_status (draft, published, cancelled, completed)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum ticket price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum ticket price"),
    search: Optional[str] = Query(None, description="Search keyword in event_name or description"),
    sort_by: Literal["event_id", "event_name", "event_date", "ticket_price", "available_tickets"] = Query("event_date"),
    order: Literal["asc", "desc"] = Query("asc"),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Retrieves events with advanced API management features:
    - Pagination (page, limit)
    - Filtering (category, venue, organiser, status, price range)
    - Full-text keyword search
    - Dynamic sorting
    """
    cursor = db.cursor()
    conditions = []
    params = []

    if category_id:
        conditions.append("e.category_id = %s")
        params.append(category_id)

    if venue_id:
        conditions.append("e.venue_id = %s")
        params.append(venue_id)

    if organiser_id:
        conditions.append("e.organiser_id = %s")
        params.append(organiser_id)

    if status:
        conditions.append("e.event_status = %s")
        params.append(status)

    if min_price is not None:
        conditions.append("e.ticket_price >= %s")
        params.append(min_price)

    if max_price is not None:
        conditions.append("e.ticket_price <= %s")
        params.append(max_price)

    if search:
        conditions.append("(e.event_name LIKE %s OR e.description LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count query
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM events e
        {where_clause}
    """
    cursor.execute(count_sql, params)
    total_items = cursor.fetchone()["total"]

    # Select query with joins
    offset = (page - 1) * limit
    order_clause = f"ORDER BY e.{sort_by} {order.upper()}"
    select_sql = f"""
        SELECT 
            e.event_id, e.organiser_id, e.venue_id, e.category_id,
            e.event_name, e.description, e.event_date, e.start_time, e.end_time,
            e.ticket_price, e.total_tickets, e.available_tickets, e.event_status, e.image_url, e.created_at,
            v.venue_name, v.location as venue_location, v.capacity as venue_capacity,
            c.category_name,
            u.full_name as organiser_name, u.email as organiser_email
        FROM events e
        JOIN venues v ON e.venue_id = v.venue_id
        JOIN categories c ON e.category_id = c.category_id
        JOIN users u ON e.organiser_id = u.user_id
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_sql, params + [limit, offset])
    events = serialize_rows(cursor.fetchall())

    total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

    return {
        "status": "success",
        "data": events,
        "pagination": {
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{event_id}", status_code=status.HTTP_200_OK)
def get_event_by_id(event_id: int, db: pymysql.Connection = Depends(get_db)):
    """Retrieves detailed information for a single event."""
    cursor = db.cursor()
    select_sql = """
        SELECT 
            e.event_id, e.organiser_id, e.venue_id, e.category_id,
            e.event_name, e.description, e.event_date, e.start_time, e.end_time,
            e.ticket_price, e.total_tickets, e.available_tickets, e.event_status, e.image_url, e.created_at,
            v.venue_name, v.location as venue_location, v.capacity as venue_capacity,
            c.category_name,
            u.full_name as organiser_name, u.email as organiser_email
        FROM events e
        JOIN venues v ON e.venue_id = v.venue_id
        JOIN categories c ON e.category_id = c.category_id
        JOIN users u ON e.organiser_id = u.user_id
        WHERE e.event_id = %s
    """
    cursor.execute(select_sql, (event_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with ID {event_id} not found.")

    return {
        "status": "success",
        "data": serialize_row(row)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Creates a new event record with initial available tickets."""
    cursor = db.cursor()

    # Validate venue exists
    cursor.execute("SELECT venue_id, capacity, approval_status FROM venues WHERE venue_id = %s", (payload.venue_id,))
    venue = cursor.fetchone()
    if not venue:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Venue ID {payload.venue_id} does not exist.")

    # Validate category exists
    cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (payload.category_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {payload.category_id} does not exist.")

    # Check capacity limit
    if payload.total_tickets > venue["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total tickets ({payload.total_tickets}) exceeds venue capacity ({venue['capacity']})."
        )

    organiser_id = current_user["user_id"]
    event_status = payload.resolved_status
    available_tickets = payload.total_tickets
    event_name = payload.resolved_name
    event_date = payload.resolved_date
    start_time = payload.resolved_start_time
    end_time = payload.resolved_end_time
    image_url = (payload.image_url or "").strip() or None

    cursor.execute("""
        INSERT INTO events (
            organiser_id, venue_id, category_id,
            event_name, description, event_date, start_time, end_time,
            ticket_price, total_tickets, available_tickets, event_status, image_url
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        organiser_id, payload.venue_id, payload.category_id,
        event_name, payload.description, event_date,
        start_time, end_time, payload.ticket_price,
        payload.total_tickets, available_tickets, event_status, image_url
    ))

    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (new_id,))
    created_event = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": f"Event '{event_name}' created successfully.",
        "data": created_event
    }

@router.put("/{event_id}", status_code=status.HTTP_200_OK)
def update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Updates event specifications. Organisers can only edit own events."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with ID {event_id} not found.")

    if current_user["role"] != "admin" and existing["organiser_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only edit your own events.")

    updates = []
    params = []

    if payload.event_name is not None:
        updates.append("event_name = %s")
        params.append(payload.event_name.strip())

    if payload.description is not None:
        updates.append("description = %s")
        params.append(payload.description)

    if payload.category_id is not None:
        updates.append("category_id = %s")
        params.append(payload.category_id)

    if payload.venue_id is not None:
        updates.append("venue_id = %s")
        params.append(payload.venue_id)

    if payload.event_date is not None:
        updates.append("event_date = %s")
        params.append(payload.event_date)

    if payload.start_time is not None:
        updates.append("start_time = %s")
        params.append(payload.start_time)

    if payload.end_time is not None:
        updates.append("end_time = %s")
        params.append(payload.end_time)

    if payload.ticket_price is not None:
        updates.append("ticket_price = %s")
        params.append(payload.ticket_price)

    if payload.total_tickets is not None:
        updates.append("total_tickets = %s")
        params.append(payload.total_tickets)

    if payload.available_tickets is not None:
        updates.append("available_tickets = %s")
        params.append(payload.available_tickets)

    if payload.event_status is not None:
        updates.append("event_status = %s")
        params.append(payload.event_status)

    if payload.image_url is not None:
        updates.append("image_url = %s")
        params.append(payload.image_url.strip() if payload.image_url else None)

    if updates:
        params.append(event_id)
        update_sql = f"UPDATE events SET {', '.join(updates)} WHERE event_id = %s"
        cursor.execute(update_sql, params)

    cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
    updated_event = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": "Event updated successfully.",
        "data": updated_event
    }

@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(
    event_id: int,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Cancels or removes an event."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event with ID {event_id} not found.")

    if current_user["role"] != "admin" and existing["organiser_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only delete your own events.")

    # Check for existing bookings
    cursor.execute("SELECT COUNT(*) as booking_cnt FROM bookings WHERE event_id = %s", (event_id,))
    booking_cnt = cursor.fetchone()["booking_cnt"]

    if booking_cnt > 0:
        # Mark as cancelled to preserve audit/financial records
        cursor.execute("UPDATE events SET event_status = 'cancelled' WHERE event_id = %s", (event_id,))
        return {
            "status": "success",
            "message": f"Event '{existing['event_name']}' has {booking_cnt} existing booking(s). Status updated to 'cancelled'."
        }

    cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    return {
        "status": "success",
        "message": f"Event '{existing['event_name']}' deleted successfully."
    }
