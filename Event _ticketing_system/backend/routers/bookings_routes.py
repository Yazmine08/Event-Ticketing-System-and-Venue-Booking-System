"""
Bookings Resource Router
Provides complete CRUD endpoints for the /bookings resource.
Integrates:
- Genuine External QR Code Generator API (api.qrserver.com / quickchart.io)
- Official PDF Generation Service
- Payment transaction generation
- Ticket QR code verification / check-in
Course: SWC3633 / SWC4443 Web API Development
"""
import uuid
import secrets
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
import pymysql

from backend.database import get_db, serialize_row, serialize_rows
from backend.models import BookingCreate, TicketVerifyRequest, BookingCancelRequest, BookingUpdate
from backend.auth import get_current_user, require_roles
from backend.external_services import fetch_external_qr_code, request_external_pdf_service

router = APIRouter(prefix="/bookings", tags=["Bookings Resource"])

@router.get("", status_code=status.HTTP_200_OK)
def list_bookings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    booking_status: Optional[str] = Query(None, description="Filter by booking status (confirmed, cancelled, pending)"),
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Retrieves bookings with role-based filtering:
    - Admin: can view all system bookings
    - Organiser: can view bookings for their hosted events
    - Customer: can view only their own ticket bookings
    """
    cursor = db.cursor()
    conditions = []
    params = []

    # RBAC Data Filtering
    if current_user["role"] == "customer":
        conditions.append("b.user_id = %s")
        params.append(current_user["user_id"])
    elif current_user["role"] == "organiser":
        conditions.append("e.organiser_id = %s")
        params.append(current_user["user_id"])
    # Admin has unrestricted view

    if event_id:
        conditions.append("b.event_id = %s")
        params.append(event_id)

    if booking_status:
        conditions.append("b.booking_status = %s")
        params.append(booking_status)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM bookings b
        JOIN events e ON b.event_id = e.event_id
        {where_clause}
    """
    cursor.execute(count_sql, params)
    total_items = cursor.fetchone()["total"]

    # Select
    offset = (page - 1) * limit
    select_sql = f"""
        SELECT 
            b.booking_id, b.user_id, b.event_id, b.quantity, b.total_amount,
            b.booking_status, b.booking_date, b.ticket_code,
            b.cancellation_reason, b.cancelled_at,
            u.full_name as customer_name, u.email as customer_email, u.phone as customer_phone,
            e.event_name, e.event_date, e.start_time, e.end_time, e.ticket_price,
            v.venue_name, v.location as venue_location,
            c.category_name,
            p.payment_id, p.payment_method, p.payment_status, p.transaction_reference, p.payment_date
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN events e ON b.event_id = e.event_id
        JOIN venues v ON e.venue_id = v.venue_id
        JOIN categories c ON e.category_id = c.category_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        {where_clause}
        ORDER BY b.booking_id DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_sql, params + [limit, offset])
    bookings = serialize_rows(cursor.fetchall())

    total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

    return {
        "status": "success",
        "data": bookings,
        "pagination": {
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/{booking_id}", status_code=status.HTTP_200_OK)
def get_booking_by_id(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """Retrieves full details for a single booking."""
    cursor = db.cursor()
    select_sql = """
        SELECT 
            b.booking_id, b.user_id, b.event_id, b.quantity, b.total_amount,
            b.booking_status, b.booking_date, b.ticket_code,
            b.cancellation_reason, b.cancelled_at,
            u.full_name as customer_name, u.email as customer_email, u.phone as customer_phone,
            e.event_name, e.event_date, e.start_time, e.end_time, e.ticket_price, e.organiser_id,
            v.venue_name, v.location as venue_location,
            c.category_name,
            p.payment_id, p.payment_method, p.payment_status, p.transaction_reference, p.payment_date
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN events e ON b.event_id = e.event_id
        JOIN venues v ON e.venue_id = v.venue_id
        JOIN categories c ON e.category_id = c.category_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.booking_id = %s
    """
    cursor.execute(select_sql, (booking_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found.")

    booking = serialize_row(row)

    # Authorization check
    if current_user["role"] == "customer" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only view your own bookings.")
    if current_user["role"] == "organiser" and booking["organiser_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only view bookings for your hosted events.")

    return {
        "status": "success",
        "data": booking
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """Creates a ticket booking, updates ticket availability, generates ticket code and payment receipt."""
    cursor = db.cursor()

    # 1. Fetch Event and check ticket availability
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (payload.event_id,))
    event = cursor.fetchone()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event ID {payload.event_id} not found.")

    if event["event_status"] != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event is not available for booking (Status: {event['event_status']})."
        )

    qty = payload.resolved_quantity
    if event["available_tickets"] < qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested {qty} tickets, but only {event['available_tickets']} remain available."
        )

    # 2. Financial calculation
    unit_price = float(event["ticket_price"])
    total_amount = round(unit_price * qty, 2)

    # 3. Generate unique Ticket Code & Transaction Reference
    ticket_code = f"TKT-{secrets.token_hex(4).upper()}"
    tx_ref = f"TXN-{secrets.token_hex(4).upper()}"
    payment_method = payload.resolved_payment_method

    # 4. Insert into bookings
    cursor.execute("""
        INSERT INTO bookings (user_id, event_id, quantity, total_amount, booking_status, ticket_code)
        VALUES (%s, %s, %s, %s, 'confirmed', %s)
    """, (current_user["user_id"], payload.event_id, qty, total_amount, ticket_code))

    booking_id = cursor.lastrowid

    # 5. Decrement event available_tickets
    cursor.execute("""
        UPDATE events
        SET available_tickets = available_tickets - %s
        WHERE event_id = %s
    """, (qty, payload.event_id))

    # 6. Insert payment record
    cursor.execute("""
        INSERT INTO payments (booking_id, payment_method, payment_amount, payment_status, transaction_reference)
        VALUES (%s, %s, %s, 'paid', %s)
    """, (booking_id, payment_method, total_amount, tx_ref))

    # 7. Fetch full created booking
    cursor.execute("""
        SELECT 
            b.booking_id, b.user_id, b.event_id, b.quantity, b.total_amount,
            b.booking_status, b.booking_date, b.ticket_code,
            e.event_name, e.event_date, e.start_time, e.end_time, e.ticket_price,
            v.venue_name, v.location as venue_location,
            p.payment_method, p.payment_status, p.transaction_reference
        FROM bookings b
        JOIN events e ON b.event_id = e.event_id
        JOIN venues v ON e.venue_id = v.venue_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.booking_id = %s
    """, (booking_id,))
    created_booking = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": f"Booking #{booking_id} confirmed successfully! Ticket code: {ticket_code}.",
        "data": created_booking
    }

@router.put("/{booking_id}", status_code=status.HTTP_200_OK)
def update_booking(
    booking_id: int,
    payload: BookingUpdate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin & Organiser] Updates a booking record (booking status, payment status, cancellation reason)."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.*, e.organiser_id 
        FROM bookings b
        JOIN events e ON b.event_id = e.event_id
        WHERE b.booking_id = %s
    """, (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found.")

    if current_user["role"] == "organiser" and booking["organiser_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only update bookings for your own events.")

    old_status = booking["booking_status"]
    new_status = payload.booking_status or old_status

    # If transitioning from active (pending/confirmed) to cancelled -> restore tickets
    if old_status != "cancelled" and new_status == "cancelled":
        cursor.execute("UPDATE events SET available_tickets = available_tickets + %s WHERE event_id = %s", (booking["quantity"], booking["event_id"]))
        cursor.execute("""
            UPDATE bookings 
            SET booking_status = 'cancelled', 
                cancellation_reason = %s, 
                cancelled_at = CURRENT_TIMESTAMP 
            WHERE booking_id = %s
        """, (payload.cancellation_reason or "Updated to cancelled by admin", booking_id))
    # If transitioning from cancelled back to confirmed -> deduct tickets if available
    elif old_status == "cancelled" and new_status == "confirmed":
        cursor.execute("SELECT available_tickets FROM events WHERE event_id = %s", (booking["event_id"],))
        ev = cursor.fetchone()
        if ev and ev["available_tickets"] < booking["quantity"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient tickets available to reactivate booking.")
        cursor.execute("UPDATE events SET available_tickets = available_tickets - %s WHERE event_id = %s", (booking["quantity"], booking["event_id"]))
        cursor.execute("UPDATE bookings SET booking_status = 'confirmed', cancellation_reason = NULL, cancelled_at = NULL WHERE booking_id = %s", (booking_id,))
    elif payload.booking_status:
        cursor.execute("UPDATE bookings SET booking_status = %s WHERE booking_id = %s", (payload.booking_status, booking_id))

    if payload.cancellation_reason and new_status == "cancelled":
        cursor.execute("UPDATE bookings SET cancellation_reason = %s WHERE booking_id = %s", (payload.cancellation_reason, booking_id))

    # Update payment status if provided
    if payload.payment_status:
        cursor.execute("UPDATE payments SET payment_status = %s WHERE booking_id = %s", (payload.payment_status, booking_id))

    # Fetch updated record
    cursor.execute("""
        SELECT b.*, u.full_name as customer_name, u.email as customer_email, e.event_name, p.payment_status, p.payment_method
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN events e ON b.event_id = e.event_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.booking_id = %s
    """, (booking_id,))
    updated = serialize_row(cursor.fetchone())

    return {
        "status": "success",
        "message": f"Booking #{booking_id} updated successfully.",
        "data": updated
    }

@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def delete_booking(
    booking_id: int,
    current_user: dict = Depends(require_roles(["admin"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin Only] Permanently removes a booking record and restores ticket inventory if needed."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found.")

    if booking["booking_status"] != "cancelled":
        cursor.execute("UPDATE events SET available_tickets = available_tickets + %s WHERE event_id = %s", (booking["quantity"], booking["event_id"]))

    cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
    return {
        "status": "success",
        "message": f"Booking #{booking_id} permanently removed."
    }

@router.put("/{booking_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_booking(
    booking_id: int,
    payload: Optional[BookingCancelRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """Cancels a booking, releases reserved tickets, marks payment as refunded, and records cancellation reason."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found.")

    if current_user["role"] != "admin" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only cancel your own bookings.")

    if booking["booking_status"] == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This booking has already been cancelled.")

    reason = payload.resolved_reason if payload else "Customer requested cancellation - Schedule conflict (Refund processed)"

    # 1. Update booking status and cancellation reason
    cursor.execute("""
        UPDATE bookings 
        SET booking_status = 'cancelled', 
            cancellation_reason = %s, 
            cancelled_at = CURRENT_TIMESTAMP 
        WHERE booking_id = %s
    """, (reason, booking_id))

    # 2. Restore available tickets
    cursor.execute("""
        UPDATE events
        SET available_tickets = available_tickets + %s
        WHERE event_id = %s
    """, (booking["quantity"], booking["event_id"]))

    # 3. Mark payment refunded
    cursor.execute("UPDATE payments SET payment_status = 'refunded' WHERE booking_id = %s", (booking_id,))

    return {
        "status": "success",
        "message": f"Booking #{booking_id} cancelled successfully. {booking['quantity']} ticket(s) released back to inventory.",
        "data": {
            "booking_id": booking_id,
            "ticket_code": booking["ticket_code"],
            "booking_status": "cancelled",
            "cancellation_reason": reason,
            "refund_status": "refunded"
        }
    }

@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def delete_booking(
    booking_id: int, 
    reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: dict = Depends(get_current_user), 
    db: pymysql.Connection = Depends(get_db)
):
    """Alias for cancelling a booking following RESTful DELETE semantics."""
    cancel_payload = BookingCancelRequest(cancellation_reason=reason) if reason else None
    return cancel_booking(booking_id, cancel_payload, current_user, db)

@router.get("/{booking_id}/qrcode", status_code=status.HTTP_200_OK)
def get_booking_qr_code(
    booking_id: int,
    format: Literal["image", "json"] = Query("image", description="Return binary image or JSON metadata"),
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Third-Party API Integration:
    Calls external QR Code Generator API to render a live QR code for admission.
    Cancelled tickets are rejected with 400 Bad Request to prevent invalid admissions.
    """
    cursor = db.cursor()
    cursor.execute("SELECT booking_id, user_id, ticket_code, booking_status, cancellation_reason, cancelled_at FROM bookings WHERE booking_id = %s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking ID {booking_id} not found.")

    if current_user["role"] == "customer" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Cannot access other users' QR tickets.")

    ticket_code = booking["ticket_code"] or f"TKT{booking['booking_id']:03d}"

    # Block QR generation for cancelled tickets
    if booking["booking_status"] == "cancelled":
        reason = booking.get("cancellation_reason") or "Customer requested cancellation"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate gate admission pass: Ticket {ticket_code} was cancelled. Reason: {reason}"
        )

    qr_result = fetch_external_qr_code(ticket_code, size=250)

    if format == "json":
        return {
            "status": "success",
            "booking_id": booking_id,
            "ticket_code": ticket_code,
            "qr_api_provider": qr_result.get("provider"),
            "qr_code_url": qr_result.get("url"),
            "latency_ms": qr_result.get("latency_ms")
        }

    if qr_result.get("bytes"):
        return Response(content=qr_result["bytes"], media_type="image/png")
    else:
        # Redirect or return URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=qr_result["url"])

@router.get("/{booking_id}/pdf", status_code=status.HTTP_200_OK)
def download_booking_pdf(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Third-Party API Integration:
    Generates an official admission PDF Ticket & Invoice with embedded external QR code.
    Cancelled tickets cannot be downloaded as admission passes.
    """
    cursor = db.cursor()
    select_sql = """
        SELECT 
            b.booking_id, b.user_id, b.quantity, b.total_amount, b.booking_status, b.ticket_code,
            b.cancellation_reason, b.cancelled_at,
            u.full_name, u.email, u.phone,
            e.event_name, e.event_date, e.start_time, e.end_time, e.ticket_price, e.organiser_id,
            v.venue_name, v.location,
            c.category_name,
            p.payment_method, p.transaction_reference
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN events e ON b.event_id = e.event_id
        JOIN venues v ON e.venue_id = v.venue_id
        JOIN categories c ON e.category_id = c.category_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.booking_id = %s
    """
    cursor.execute(select_sql, (booking_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking ID {booking_id} not found.")

    booking_data = serialize_row(row)

    if current_user["role"] == "customer" and booking_data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Cannot download other users' tickets.")

    ticket_code = booking_data.get("ticket_code") or f"TKT{booking_id:03d}"

    # Block PDF generation for cancelled tickets
    if booking_data["booking_status"] == "cancelled":
        reason = booking_data.get("cancellation_reason") or "Customer requested cancellation"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot download admission pass: Booking #{booking_id} (Ticket {ticket_code}) has been cancelled and invalidated. Reason: {reason}"
        )

    # Fetch external QR code
    qr_res = fetch_external_qr_code(ticket_code, size=200)
    qr_bytes = qr_res.get("bytes")

    # Generate PDF document
    pdf_bytes = request_external_pdf_service(booking_data, qr_bytes)

    filename = f"Ticket_{ticket_code}_{booking_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Generated-By": "EventTicketing-PDF-API"
        }
    )

@router.post("/verify-ticket", status_code=status.HTTP_200_OK)
def verify_ticket(
    payload: TicketVerifyRequest,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Ticket Gate Verification Endpoint:
    Allows organisers or administrators to scan/verify a ticket code at admission checkpoints.
    """
    ticket_code = payload.code
    cursor = db.cursor()
    select_sql = """
        SELECT 
            b.booking_id, b.ticket_code, b.booking_status, b.quantity, b.total_amount,
            b.cancellation_reason, b.cancelled_at,
            u.full_name as customer_name, u.email as customer_email,
            e.event_name, e.event_date, e.start_time, e.end_time, e.organiser_id,
            v.venue_name, v.location as venue_location
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN events e ON b.event_id = e.event_id
        JOIN venues v ON e.venue_id = v.venue_id
        WHERE b.ticket_code = %s
    """
    cursor.execute(select_sql, (ticket_code,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket code '{ticket_code}' not found in system database."
        )

    booking = serialize_row(row)

    # Organisers can only verify tickets for their own events
    if current_user["role"] == "organiser" and booking["organiser_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This ticket belongs to an event hosted by another organiser."
        )

    is_valid = (booking["booking_status"] == "confirmed")
    reason_info = f" (Reason: {booking['cancellation_reason']})" if booking.get("cancellation_reason") else ""
    message = "Ticket Verified: ADMIT PASSENGER" if is_valid else f"Ticket Invalid: Status is '{booking['booking_status']}'{reason_info}"

    return {
        "status": "success",
        "valid": is_valid,
        "message": message,
        "data": booking
    }
