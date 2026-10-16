# RESTful Web API Documentation
**Course**: SWC3633 / SWC4443 Web API Development  
**Institution**: Universiti Poly-Tech Malaysia (UPTM)  
**System**: Event Ticketing and Venue Booking RESTful Web API  
**Base URL**: `http://127.0.0.1:8000` (or `http://localhost/event_ticketing_system`)  
**Specification Version**: 1.0.0 (OpenAPI 3.1 compliant)  

---

## 🔐 Authentication & Authorization Standard

The API implements dual-layer stateless authentication:
1. **JSON Web Token (JWT Bearer)**:
   - Header: `Authorization: Bearer <access_token>`
   - Generated via `POST /api/auth/login` or `POST /auth/login`. Token validity: 24 Hours.
2. **API Key Authentication**:
   - Header: `X-API-Key: <user_api_key>`
   - Suitable for automated backend-to-backend integrations and headless testing.
3. **Role-Based Access Control (RBAC)**:
   - `admin`: Global administrative privileges (User management, venue approvals, system audit logs).
   - `organiser`: Event publishing, capacity scheduling, admission ticket gate validation.
   - `customer`: Public event exploration, booking placement, payment receipt, live QR code ticket generation, and cancellation.

---

## 📌 Resource Endpoints Summary

| Resource | Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `/api/auth/register` | `POST` | Public | Register new user account with automatic bcrypt hash |
| **Auth** | `/api/auth/login` | `POST` | Public | Authenticate user & return signed JWT token |
| **Auth** | `/api/auth/me` | `GET` | Any Authenticated | Retrieve profile details of currently logged-in user |
| **Users** | `/api/users` | `GET` | `admin` | Retrieve paginated user list with role filters & search |
| **Users** | `/api/users/{id}` | `GET` | `admin` or Self | Retrieve single user record by ID |
| **Users** | `/api/users` | `POST` | `admin` | Create new user with specific assigned role |
| **Users** | `/api/users/{id}` | `PUT` | `admin` or Self | Update user details (Name, email, phone, role) |
| **Users** | `/api/users/{id}` | `DELETE` | `admin` | Remove user record from system (Cascade deletes) |
| **Venues** | `/api/venues` | `GET` | Public | List approved venues (with filter & pagination) |
| **Venues** | `/api/venues/{id}` | `GET` | Public | Get venue details by ID |
| **Venues** | `/api/venues` | `POST` | `admin`, `organiser` | Register new venue |
| **Venues** | `/api/venues/{id}` | `PUT` | `admin` | Update venue details or approve venue status |
| **Venues** | `/api/venues/{id}` | `DELETE` | `admin` | Delete venue (Integrity protected) |
| **Events** | `/api/events` | `GET` | Public | List published events with search, genre & sorting |
| **Events** | `/api/events/{id}` | `GET` | Public | Get single event details with venue & organiser info |
| **Events** | `/api/events` | `POST` | `admin`, `organiser` | Create new event listing |
| **Events** | `/api/events/{id}` | `PUT` | `admin`, Organiser owner | Update event listing or modify status |
| **Events** | `/api/events/{id}` | `DELETE` | `admin`, Organiser owner | Delete event listing |
| **Bookings** | `/api/bookings` | `GET` | Any Authenticated | List bookings (Filtered by user ID or all for Admin) |
| **Bookings** | `/api/bookings/{id}` | `GET` | Any Authenticated | Retrieve specific booking invoice & details |
| **Bookings** | `/api/bookings` | `POST` | `customer`, `admin` | Place new booking with automated ticket allocation |
| **Bookings** | `/api/bookings/{id}/cancel` | `PUT` | Booking Owner, `admin` | Cancel booking & release reserved ticket inventory |
| **Bookings** | `/api/bookings/{id}/qrcode` | `GET` | Public / Owner | Fetch dynamic admission QR Code from external API |
| **Bookings** | `/api/bookings/{id}/pdf` | `GET` | Owner, `admin` | Download printable official PDF ticket pass |
| **Bookings** | `/api/bookings/verify-ticket` | `POST` | `admin`, `organiser` | Gate scanner API to validate attendee admission pass |
| **Categories**| `/api/categories` | `GET` | Public | List all available event categories |
| **Categories**| `/api/categories` | `POST` | `admin` | Add new category |
| **Stats** | `/api/stats/health` | `GET` | Public | Server & MySQL database connection health check |
| **Stats** | `/api/stats/summary` | `GET` | `admin` | Aggregated metrics (Revenue, user counts, bookings) |
| **Stats** | `/api/stats/external-apis` | `GET` | `admin` | Live audit logs & latency telemetry of external APIs |

*Note: All endpoints are also accessible without `/api` prefix (e.g., `/events`, `/users`, `/venues`, `/bookings`) for complete REST architectural compatibility.*

---

## 📖 Detailed Endpoint Specifications

### 1. Authentication Endpoints

#### `POST /api/auth/register`
- **Purpose**: Registers a new customer or organiser account.
- **Request Body**:
```json
{
  "full_name": "John Doe",
  "email": "johndoe@example.com",
  "password": "password123",
  "phone": "0123456789",
  "role": "customer"
}
```
- **Response** (`201 Created`):
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user_id": 6,
    "full_name": "John Doe",
    "email": "johndoe@example.com",
    "role": "customer",
    "api_key": "cus_live_key_e5349f7ba3089d42"
  }
}
```
- **Status Codes**:
  - `201 Created`: Registration successful.
  - `400 Bad Request`: Email already registered or invalid input schema.

---

#### `POST /api/auth/login`
- **Purpose**: Authenticates user credentials and generates a signed JWT token.
- **Request Body**:
```json
{
  "email": "sarah@example.com",
  "password": "password123"
}
```
- **Response** (`200 OK`):
```json
{
  "status": "success",
  "token_type": "bearer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": 4,
    "full_name": "Sarah Ahmad",
    "email": "sarah@example.com",
    "role": "customer",
    "api_key": "cus_live_key_aaaabbbbccccdddd"
  }
}
```
- **Status Codes**:
  - `200 OK`: Login successful.
  - `401 Unauthorized`: Invalid email or password.

---

### 2. Events Resource Endpoints

#### `GET /api/events`
- **Purpose**: Retrieves a paginated list of events with dynamic filtering, full-text search, and sorting.
- **Query Parameters**:
  - `search` (string, optional): Search keyword against event title and description.
  - `category_id` (int, optional): Filter by genre/category.
  - `venue_id` (int, optional): Filter by hosting venue.
  - `status` (string, optional, default: `published`): Filter by event status.
  - `page` (int, default: 1): Page number.
  - `limit` (int, default: 10): Records per page.
  - `sort_by` (string, default: `event_date`): Sort column (`event_date`, `ticket_price`, `event_name`).
  - `order` (string, default: `asc`): Sort direction (`asc` or `desc`).
- **Response** (`200 OK`):
```json
{
  "status": "success",
  "data": [
    {
      "event_id": 1,
      "organiser_id": 2,
      "venue_id": 1,
      "category_id": 1,
      "event_name": "Malaysia Music Festival",
      "description": "Live music festival featuring local artists",
      "event_date": "2026-11-15",
      "start_time": "18:00:00",
      "end_time": "23:00:00",
      "ticket_price": 120.0,
      "total_tickets": 2500,
      "available_tickets": 2498,
      "event_status": "published",
      "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819",
      "venue_name": "KL Convention Centre",
      "venue_location": "Kuala Lumpur",
      "category_name": "Music",
      "organiser_name": "Aina Rahman"
    }
  ],
  "pagination": {
    "total_items": 5,
    "page": 1,
    "limit": 10,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

#### `POST /api/events`
- **Purpose**: Creates a new event listing (Restricted to `admin` and `organiser`).
- **Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`
- **Request Body**:
```json
{
  "event_name": "AI & Web API Conference 2026",
  "venue_id": 1,
  "category_id": 2,
  "description": "Annual international tech summit.",
  "event_date": "2026-12-20",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "ticket_price": 150.00,
  "total_tickets": 500,
  "image_url": "https://images.unsplash.com/photo-tech.jpg"
}
```
- **Response** (`201 Created`):
```json
{
  "status": "success",
  "message": "Event created successfully",
  "event_id": 6
}
```
- **Status Codes**:
  - `201 Created`: Event successfully registered.
  - `400 Bad Request`: Allocated tickets exceed hosting venue capacity.
  - `403 Forbidden`: Authenticated user does not have permission (`customer` cannot create events).

---

### 3. Bookings Resource Endpoints

#### `POST /api/bookings`
- **Purpose**: Purchases tickets for an event. Automatically calculates total cost, generates unique ticket code, records payment, and decrements available ticket inventory atomically.
- **Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`
- **Request Body**:
```json
{
  "event_id": 1,
  "quantity": 2,
  "payment_method": "online_banking"
}
```
- **Response** (`201 Created`):
```json
{
  "status": "success",
  "message": "Booking confirmed successfully",
  "booking_id": 6,
  "ticket_code": "TKT-A92B-3C4D",
  "total_amount": 240.0,
  "payment_status": "paid",
  "qr_url": "/api/bookings/6/qrcode",
  "pdf_url": "/api/bookings/6/pdf"
}
```
- **Status Codes**:
  - `201 Created`: Booking completed.
  - `400 Bad Request`: Insufficient tickets available or event not published.
  - `401 Unauthorized`: Authentication missing.

---

#### `GET /api/bookings/{id}/qrcode`
- **Purpose**: Communicates with the external QR Code Generator API (`api.qrserver.com`) to generate an admission QR pass.
- **Parameters**: `format=image` (returns binary image) or `format=json` (returns metadata & external CDN URL).
- **Response** (`200 OK` with `Content-Type: image/png`):
  - Binary PNG image data containing ticket validation payload.

---

#### `GET /api/bookings/{id}/pdf`
- **Purpose**: Compiles and delivers a downloadable PDF e-ticket pass containing event schedule, venue address, invoice breakdown, and the embedded live external QR code.
- **Headers**: `Authorization: Bearer <token>` or query `?token=...`
- **Response** (`200 OK` with `Content-Type: application/pdf`):
  - Binary PDF document stream (`Content-Disposition: attachment; filename="ticket_TKT001.pdf"`).

---

#### `POST /api/bookings/verify-ticket`
- **Purpose**: Gate validator used by Organisers and Admins to scan/verify ticket authenticity at venue gates.
- **Request Body**:
```json
{
  "ticket_code": "TKT001"
}
```
- **Response** (`200 OK`):
```json
{
  "status": "success",
  "valid": true,
  "message": "Valid Admission Ticket. Admit 2 attendee(s).",
  "booking": {
    "booking_id": 1,
    "ticket_code": "TKT001",
    "event_name": "Malaysia Music Festival",
    "attendee_name": "Sarah Ahmad",
    "quantity": 2,
    "booking_status": "confirmed"
  }
}
```

---

### 4. Venues Resource Endpoints

#### `GET /api/venues`
- **Purpose**: Lists all venues with filtering on approval status and capacity.
- **Query Parameters**: `approval_status`, `page`, `limit`.
- **Response** (`200 OK`):
```json
{
  "status": "success",
  "data": [
    {
      "venue_id": 1,
      "venue_name": "KL Convention Centre",
      "location": "Kuala Lumpur",
      "capacity": 3000,
      "description": "Convention and exhibition venue",
      "approval_status": "approved"
    }
  ]
}
```

---

#### `PUT /api/venues/{id}`
- **Purpose**: Updates venue details and approves/rejects pending venues (`admin` only).
- **Request Body**:
```json
{
  "approval_status": "approved"
}
```
- **Response** (`200 OK`):
```json
{
  "status": "success",
  "message": "Venue updated successfully"
}
```

---

## 🛡️ Centralized Error Responses

Every error across all endpoints returns a consistent standardized JSON schema:

```json
{
  "status": "error",
  "detail": "Descriptive human-readable explanation of error.",
  "status_code": 400
}
```

Standard HTTP Status Codes Used:
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Input data validation failure or business rule violation.
- `401 Unauthorized`: Missing, invalid, or expired credentials.
- `403 Forbidden`: Authenticated user lacks RBAC permissions for resource.
- `404 Not Found`: Target resource does not exist in database.
- `429 Too Many Requests`: Client exceeded rate limit (>120 requests/minute).
- `500 Internal Server Error`: Server exception with automatic diagnostic logging.
