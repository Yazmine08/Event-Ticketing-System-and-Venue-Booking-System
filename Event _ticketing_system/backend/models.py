"""
Pydantic Request Validation Models and Schemas
Matching the MySQL database schema for event_ticketing_db.
Enforces strict type-checking, bounds, and provides backward-compatible field aliases.
"""
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field

# ----------------- USER MODELS -----------------

class UserRegister(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, example="Sarah Ahmad")
    name: Optional[str] = Field(None, min_length=2, max_length=100, example="Sarah Ahmad")
    email: EmailStr = Field(..., example="sarah@example.com")
    password: str = Field(..., min_length=6, max_length=100, example="password123")
    role: Literal["customer", "organiser"] = Field(default="customer", example="customer")
    phone: Optional[str] = Field(None, max_length=20, example="0124444444")

    @property
    def display_name(self) -> str:
        return (self.full_name or self.name or "User").strip()

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="admin@example.com")
    password: str = Field(..., min_length=4, example="password123")

class UserCreateAdmin(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, example="Admin EventHub")
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: EmailStr = Field(..., example="newadmin@example.com")
    password: str = Field(..., min_length=6, example="password123")
    role: Literal["admin", "organiser", "customer"] = Field(default="customer")
    phone: Optional[str] = Field(None, max_length=20, example="0121111111")

    @property
    def display_name(self) -> str:
        return (self.full_name or self.name or "User").strip()

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[Literal["admin", "organiser", "customer"]] = None
    password: Optional[str] = Field(None, min_length=6)

    @property
    def display_name(self) -> Optional[str]:
        val = self.full_name or self.name
        return val.strip() if val else None

# ----------------- VENUE MODELS -----------------

class VenueCreate(BaseModel):
    venue_name: Optional[str] = Field(None, min_length=3, max_length=150, example="KL Convention Centre")
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    location: Optional[str] = Field(None, min_length=2, max_length=255, example="Kuala Lumpur")
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    capacity: int = Field(..., gt=0, example=3000)
    description: Optional[str] = Field(None, example="Convention and exhibition venue")
    approval_status: Optional[Literal["pending", "approved", "rejected"]] = Field("approved")

    @property
    def resolved_name(self) -> str:
        return (self.venue_name or self.name or "Venue").strip()

    @property
    def resolved_location(self) -> str:
        if self.location:
            return self.location.strip()
        loc = []
        if self.address: loc.append(self.address.strip())
        if self.city: loc.append(self.city.strip())
        return ", ".join(loc) or "Kuala Lumpur"

class VenueUpdate(BaseModel):
    venue_name: Optional[str] = Field(None, min_length=3, max_length=150)
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    location: Optional[str] = Field(None, min_length=2, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    approval_status: Optional[Literal["pending", "approved", "rejected"]] = None

    @property
    def resolved_name(self) -> Optional[str]:
        val = self.venue_name or self.name
        return val.strip() if val else None

    @property
    def resolved_location(self) -> Optional[str]:
        if self.location:
            return self.location.strip()
        loc = []
        if self.address: loc.append(self.address.strip())
        if self.city: loc.append(self.city.strip())
        return ", ".join(loc) if loc else None

# ----------------- CATEGORY MODELS -----------------

class CategoryCreate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=2, max_length=100, example="Music")
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, example="Concerts and live performances")

    @property
    def resolved_name(self) -> str:
        return (self.category_name or self.name or "Category").strip()

# ----------------- EVENT MODELS -----------------

class EventCreate(BaseModel):
    event_name: Optional[str] = Field(None, min_length=3, max_length=150, example="Malaysia Music Festival")
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, example="Live music festival featuring local artists")
    venue_id: int = Field(..., gt=0, example=1)
    category_id: int = Field(..., gt=0, example=1)
    event_date: Optional[str] = Field(None, example="2026-11-15")
    start_time: str = Field(..., example="18:00:00")
    end_time: str = Field(..., example="23:00:00")
    ticket_price: float = Field(..., ge=0, example=120.00)
    total_tickets: int = Field(..., gt=0, example=2500)
    event_status: Optional[Literal["draft", "published", "cancelled", "completed"]] = Field("published")
    status: Optional[Literal["draft", "published", "cancelled", "completed"]] = None
    image_url: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1514525253161-7a46d19cd819")

    @property
    def resolved_name(self) -> str:
        return (self.event_name or self.title or "Event").strip()

    @property
    def resolved_status(self) -> str:
        return self.event_status or self.status or "published"

    @property
    def resolved_date(self) -> str:
        if self.event_date:
            return self.event_date.strip()
        # Parse from start_time if in YYYY-MM-DD HH:MM:SS format
        if " " in self.start_time:
            return self.start_time.split(" ")[0]
        if "T" in self.start_time:
            return self.start_time.split("T")[0]
        return "2026-12-01"

    @property
    def resolved_start_time(self) -> str:
        st = self.start_time
        if " " in st:
            return st.split(" ")[1]
        if "T" in st:
            return st.split("T")[1]
        return st

    @property
    def resolved_end_time(self) -> str:
        et = self.end_time
        if " " in et:
            return et.split(" ")[1]
        if "T" in et:
            return et.split("T")[1]
        return et

class EventUpdate(BaseModel):
    event_name: Optional[str] = Field(None, min_length=3, max_length=150)
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    venue_id: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    ticket_price: Optional[float] = Field(None, ge=0)
    total_tickets: Optional[int] = Field(None, gt=0)
    available_tickets: Optional[int] = Field(None, ge=0)
    event_status: Optional[Literal["draft", "published", "cancelled", "completed"]] = None
    status: Optional[Literal["draft", "published", "cancelled", "completed"]] = None
    image_url: Optional[str] = None

    @property
    def resolved_name(self) -> Optional[str]:
        val = self.event_name or self.title
        return val.strip() if val else None

    @property
    def resolved_status(self) -> Optional[str]:
        return self.event_status or self.status

# ----------------- BOOKING MODELS -----------------

class BookingCreate(BaseModel):
    event_id: int = Field(..., gt=0, example=1)
    quantity: Optional[int] = Field(None, gt=0, le=20, example=2)
    num_tickets: Optional[int] = Field(None, gt=0, le=20, example=2)
    payment_method: Optional[str] = Field("card", example="card")

    @property
    def resolved_quantity(self) -> int:
        return self.quantity or self.num_tickets or 1

    @property
    def resolved_payment_method(self) -> str:
        pm = (self.payment_method or "card").lower()
        if "bank" in pm or "fpx" in pm:
            return "online_banking"
        if "wallet" in pm or "pay" in pm:
            return "ewallet"
        if "cash" in pm:
            return "cash"
        return "card"

class TicketVerifyRequest(BaseModel):
    ticket_code: Optional[str] = Field(None, min_length=3, max_length=100, example="TKT001")
    booking_reference: Optional[str] = Field(None, min_length=3, max_length=100, example="TKT001")

    @property
    def code(self) -> str:
        return (self.ticket_code or self.booking_reference or "").strip()

class BookingCancelRequest(BaseModel):
    cancellation_reason: Optional[str] = Field(None, max_length=255, example="Schedule conflict - Change of plans")
    reason: Optional[str] = Field(None, max_length=255)

    @property
    def resolved_reason(self) -> str:
        r = (self.cancellation_reason or self.reason or "").strip()
        return r if r else "Customer requested cancellation - Schedule conflict (Refund processed)"

class BookingUpdate(BaseModel):
    booking_status: Optional[Literal["pending", "confirmed", "cancelled"]] = None
    payment_status: Optional[Literal["pending", "paid", "failed", "refunded"]] = None
    cancellation_reason: Optional[str] = None


