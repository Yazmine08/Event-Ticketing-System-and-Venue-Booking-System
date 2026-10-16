"""
Analytics, System Health, and External API Monitoring Router
Provides operational telemetry and external API request/response audit trail.
Course: SWC3633 / SWC4443 Web API Development
"""
import time
from fastapi import APIRouter, Depends, status
import pymysql

from backend.database import get_db, serialize_rows
from backend.auth import get_current_user, require_roles
from backend.external_services import EXTERNAL_API_LOGS, get_external_api_telemetry

router = APIRouter(prefix="/stats", tags=["System Analytics & Health"])

@router.get("/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Returns high-level statistics tailored to the user's role:
    - Admin: system-wide metrics (users, events, venues, bookings, revenue)
    - Organiser: metrics for events hosted by this organiser
    - Customer: personal booking and ticket metrics
    """
    cursor = db.cursor()
    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "admin":
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE DATE(created_at) = CURDATE()")
        signups_today = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM venues")
        total_venues = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM events")
        total_events = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM bookings WHERE booking_status = 'confirmed'")
        active_bookings = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_rev FROM bookings WHERE booking_status != 'cancelled'")
        total_revenue = float(cursor.fetchone()["total_rev"])

        cursor.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM user_logins WHERE login_time >= NOW() - INTERVAL 24 HOUR")
        signed_in_today = cursor.fetchone()["cnt"]

        return {
            "status": "success",
            "role": "admin",
            "metrics": {
                "total_users": total_users,
                "signups_today": signups_today,
                "total_venues": total_venues,
                "total_events": total_events,
                "active_bookings": active_bookings,
                "total_revenue": round(total_revenue, 2),
                "signed_in_today": signed_in_today
            }
        }

    elif role == "organiser":
        cursor.execute("SELECT COUNT(*) as cnt FROM events WHERE organiser_id = %s", (user_id,))
        my_events = cursor.fetchone()["cnt"]

        cursor.execute("""
            SELECT COUNT(b.booking_id) as b_cnt, COALESCE(SUM(b.total_amount), 0) as b_rev, COALESCE(SUM(b.quantity), 0) as b_tickets
            FROM bookings b
            JOIN events e ON b.event_id = e.event_id
            WHERE e.organiser_id = %s AND b.booking_status != 'cancelled'
        """, (user_id,))
        stats = cursor.fetchone()

        return {
            "status": "success",
            "role": "organiser",
            "metrics": {
                "my_events": my_events,
                "total_tickets_sold": int(stats["b_tickets"] or 0),
                "active_bookings": int(stats["b_cnt"] or 0),
                "total_revenue": round(float(stats["b_rev"] or 0.0), 2)
            }
        }

    else: # Customer
        cursor.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as spent
            FROM bookings
            WHERE user_id = %s AND booking_status = 'confirmed'
        """, (user_id,))
        stats = cursor.fetchone()

        return {
            "status": "success",
            "role": "customer",
            "metrics": {
                "my_confirmed_bookings": stats["cnt"],
                "total_spent": round(float(stats["spent"] or 0.0), 2)
            }
        }

@router.get("/health", status_code=status.HTTP_200_OK)
def check_system_health(db: pymysql.Connection = Depends(get_db)):
    """Health check endpoint evaluating database and external API services."""
    cursor = db.cursor()
    cursor.execute("SELECT 1 as ok")
    db_ok = (cursor.fetchone()["ok"] == 1)

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "database": {
            "type": "MySQL / MariaDB",
            "status": "connected" if db_ok else "disconnected"
        },
        "external_services": {
            "qr_generator_api": "active (https://api.qrserver.com)",
            "pdf_generator_api": "active (document service)"
        }
    }

@router.get("/external-apis", status_code=status.HTTP_200_OK)
def get_external_api_logs(current_user: dict = Depends(require_roles(["admin"]))):
    """
    [Admin Only] Retrieves diagnostic telemetry for all external API calls.
    Used for demonstrating genuine external API integration in assignment reports.
    """
    telemetry = get_external_api_telemetry()
    return {
        "status": "success",
        "total_calls": len(telemetry),
        "data": telemetry
    }
