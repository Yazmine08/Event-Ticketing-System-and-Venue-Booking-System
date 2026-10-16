# Entity Relationship Diagram (ERD) & Database Specification
**Course**: SWC3633 / SWC4443 Web API Development  
**Institution**: Universiti Poly-Tech Malaysia (UPTM)  
**System**: Event Ticketing and Venue Booking RESTful Web API  
**Database**: MySQL / MariaDB (`event_ticketing_db`)  

---

## 1. Visual Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    USERS ||--o{ EVENTS : organizes
    USERS ||--o{ BOOKINGS : places
    VENUES ||--o{ EVENTS : hosts
    CATEGORIES ||--o{ EVENTS : classifies
    EVENTS ||--o{ BOOKINGS : contains
    BOOKINGS ||--|| PAYMENTS : settles

    USERS {
        int user_id PK "Auto Increment"
        varchar full_name "User Full Name"
        varchar email UK "Unique Email Address"
        varchar password_hash "Bcrypt Hashed (Cost 10)"
        varchar phone "Contact Number"
        enum role "admin, organiser, customer"
        varchar api_key UK "Unique API Key (X-API-Key)"
        timestamp created_at "Registration Timestamp"
    }

    VENUES {
        int venue_id PK "Auto Increment"
        varchar venue_name "Name of Hall / Arena"
        varchar location "Geographic City / Address"
        int capacity "Maximum Seating Capacity"
        text description "Venue Facilities & Details"
        enum approval_status "pending, approved, rejected"
    }

    CATEGORIES {
        int category_id PK "Auto Increment"
        varchar category_name UK "Music, Tech, Sports, etc."
        text description "Category Scope Description"
    }

    EVENTS {
        int event_id PK "Auto Increment"
        int organiser_id FK "References USERS(user_id)"
        int venue_id FK "References VENUES(venue_id)"
        int category_id FK "References CATEGORIES(category_id)"
        varchar event_name "Title of the Event"
        text description "Detailed Itinerary & Agenda"
        date event_date "Date of the Event"
        time start_time "Commencement Time"
        time end_time "Conclusion Time"
        decimal ticket_price "Single Ticket Price (RM)"
        int total_tickets "Total Allocated Capacity"
        int available_tickets "Real-time Remaining Tickets"
        enum event_status "draft, published, cancelled, completed"
        mediumtext image_url "Promotional Banner Media URL"
        timestamp created_at "Creation Timestamp"
    }

    BOOKINGS {
        int booking_id PK "Auto Increment"
        int user_id FK "References USERS(user_id)"
        int event_id FK "References EVENTS(event_id)"
        int quantity "Number of Tickets Purchased"
        decimal total_amount "Total Calculated Cost (RM)"
        enum booking_status "pending, confirmed, cancelled"
        timestamp booking_date "Booking Timestamp"
        varchar ticket_code UK "Unique Cryptographic Ticket Code"
        varchar cancellation_reason "Optional Reason for Revocation"
        timestamp cancelled_at "Revocation Timestamp"
    }

    PAYMENTS {
        int payment_id PK "Auto Increment"
        int booking_id FK "References BOOKINGS(booking_id)"
        enum payment_method "online_banking, card, ewallet, cash"
        decimal payment_amount "Total Transaction Amount (RM)"
        enum payment_status "pending, paid, failed, refunded"
        varchar transaction_reference UK "External Bank/Gateway Ref"
        timestamp payment_date "Payment Settlement Timestamp"
    }
```

---

## 2. Relational Cardinalities & Business Rules

| Relationship | Cardinality | Business Description & Integrity Rule |
| :--- | :--- | :--- |
| **USERS -> EVENTS** | `1 : N` (One-to-Many) | An organiser can create and manage zero or more events. An event is owned by exactly one organiser (`organiser_id`). If an organiser account is purged, child events cascade delete. |
| **VENUES -> EVENTS** | `1 : N` (One-to-Many) | A venue can host multiple events over different dates. An event must be hosted at exactly one approved venue. `ON DELETE RESTRICT` protects venues with scheduled events. |
| **CATEGORIES -> EVENTS** | `1 : N` (One-to-Many) | A category groups multiple events. Each event belongs to one primary genre/category. `ON DELETE RESTRICT` ensures catalog consistency. |
| **EVENTS -> BOOKINGS** | `1 : N` (One-to-Many) | An event can receive many customer bookings. Each booking pertains to a single event. Buying a ticket triggers an atomic decrement of `available_tickets`. |
| **USERS -> BOOKINGS** | `1 : N` (One-to-Many) | A customer can make multiple bookings. Each booking belongs strictly to one customer. Customers can only view and manage their own bookings (RBAC). |
| **BOOKINGS -> PAYMENTS** | `1 : 1` (One-to-One) | Each booking record generates a corresponding payment transaction. Successful payment confirmation transitions the booking from `pending` to `confirmed`. |

---

## 3. Data Integrity & Constraints

1. **Entity Integrity (Primary Keys)**:
   - All tables enforce integer auto-increment primary keys (`user_id`, `venue_id`, `category_id`, `event_id`, `booking_id`, `payment_id`).
2. **Referential Integrity (Foreign Keys)**:
   - Cascading deletes are enforced on direct user associations (`organiser_id`, `user_id` in bookings).
   - Restrictive constraints prevent accidental deletion of venues or categories that have active scheduled events.
3. **Unique Keys (Uniqueness Enforcements)**:
   - `users.email`: Guarantees unique login credentials.
   - `users.api_key`: Guarantees secure deterministic API key authentication.
   - `categories.category_name`: Prevents duplicate genres.
   - `bookings.ticket_code`: Cryptographically unique QR pass identifier (`TKT-UUID-CODE`).
   - `payments.transaction_reference`: Prevents duplicate transaction settlements.
4. **Domain Integrity**:
   - ENUM types constrain valid states for roles (`admin`, `organiser`, `customer`), venue approval (`pending`, `approved`, `rejected`), event status (`draft`, `published`, `cancelled`, `completed`), booking status (`pending`, `confirmed`, `cancelled`), and payment status (`pending`, `paid`, `failed`, `refunded`).
   - Monetary values (`ticket_price`, `total_amount`, `payment_amount`) are explicitly stored as `DECIMAL(10,2)` to prevent floating-point calculation inaccuracies.
