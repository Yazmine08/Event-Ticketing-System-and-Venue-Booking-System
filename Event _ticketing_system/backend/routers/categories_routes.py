"""
Categories Resource Router
Provides endpoints for retrieving and managing event categories.
Course: SWC3633 / SWC4443 Web API Development
"""
from fastapi import APIRouter, Depends, HTTPException, status
import pymysql

from backend.database import get_db, serialize_rows
from backend.models import CategoryCreate
from backend.auth import require_roles

router = APIRouter(prefix="/categories", tags=["Categories Resource"])

@router.get("", status_code=status.HTTP_200_OK)
def list_categories(db: pymysql.Connection = Depends(get_db)):
    """Retrieves all event categories with event count."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.category_id, c.category_name, c.description, COUNT(e.event_id) as event_count
        FROM categories c
        LEFT JOIN events e ON c.category_id = e.category_id AND (e.event_status IS NULL OR e.event_status != 'cancelled')
        GROUP BY c.category_id, c.category_name, c.description
        ORDER BY c.category_id ASC
    """)
    rows = cursor.fetchall()
    return {
        "status": "success",
        "data": serialize_rows(rows)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: dict = Depends(require_roles(["admin", "organiser"])),
    db: pymysql.Connection = Depends(get_db)
):
    """[Admin / Organiser] Creates a new category."""
    cursor = db.cursor()
    cat_name = payload.resolved_name
    cursor.execute("SELECT category_id, category_name, description FROM categories WHERE LOWER(category_name) = LOWER(%s)", (cat_name.strip(),))
    existing = cursor.fetchone()
    if existing:
        return {
            "status": "success",
            "message": f"Category '{cat_name}' already exists.",
            "data": existing
        }

    cursor.execute("""
        INSERT INTO categories (category_name, description)
        VALUES (%s, %s)
    """, (cat_name.strip(), payload.description or f"{cat_name} events"))

    cat_id = cursor.lastrowid
    return {
        "status": "success",
        "message": f"Category '{cat_name}' created successfully.",
        "data": {"category_id": cat_id, "category_name": cat_name.strip(), "description": payload.description, "event_count": 0}
    }
