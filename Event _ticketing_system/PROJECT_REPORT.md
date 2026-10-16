# Academic Project Report
**Course Code**: SWC3633 / SWC4443 Web API Development  
**Session**: AUGUST 2026  
**Institution**: Universiti Poly-Tech Malaysia (UPTM)  
**Programme**: Bachelor of Information Technology (Honours)  
**Project Title**: Development of a RESTful Web API for an Event Ticketing and Venue Booking System  

---

## 1. System Overview

### 1.1 Background & Objectives
The Event Ticketing and Venue Booking System is a full-stack, enterprise-grade RESTful application developed to solve modern event discovery, venue allocation, ticket inventory reservation, and admission validation challenges. Developed to fulfil **Course Learning Outcome 3 (CLO3: Construct RESTful applications using appropriate methodologies - P4, PLO3)**, the system provides a robust backend API service paired with interactive web client interfaces.

### 1.2 Target Users
1. **Administrators**: System overseers responsible for approving registered venues, managing user accounts and roles, and monitoring system telemetry.
2. **Organisers**: Event hosts who publish upcoming concerts, conferences, and sports events, define pricing and seating capacities, and validate attendee QR codes at entrance gates.
3. **Customers**: End-users who search and filter events, book tickets, settle transactions, and download official PDF admission tickets.

### 1.3 Key Features
- **RESTful Resource Management**: Full CRUD operations for `/users`, `/events`, `/venues`, `/bookings`, and `/categories`.
- **Security & RBAC**: Dual-layer authentication via stateless JSON Web Tokens (JWT HS256) and API Key protection (`X-API-Key`), backed by Bcrypt password hashing.
- **Advanced Middleware**: Request logging, IP-based sliding-window rate limiting (120 req/min), and centralized JSON error handling.
- **API Management**: Dynamic pagination, parameter filtering, keyword search, and column sorting.
- **Genuine External Cloud APIs**: Live integration with external QR Code Generator APIs (`api.qrserver.com` & `quickchart.io`) and a PDF generation engine.

---

## 2. Database Design

### 2.1 Database Specification
- **Engine**: MySQL / MariaDB (InnoDB, UTF-8 Unicode)
- **Database Name**: `event_ticketing_db`
- **Core Entities**: `users`, `venues`, `categories`, `events`, `bookings`, `payments`

### 2.2 Entity Relationship Diagram (ERD)
The database structure establishes strict referential integrity with foreign key cascading and RESTRICT constraints. (See [erd_diagram.md](file:///C:/xampp/htdocs/event_ticketing_system/database/erd_diagram.md) for full visual diagram).

### 2.3 SQL Scripts
- **DDL Script**: `database/ddl.sql` creates all 6 relational tables with primary keys, unique constraints, and foreign key references.
- **DML Script**: `database/dml.sql` seeds at least 5 complete sample records per table, including pre-hashed bcrypt accounts and realistic event schedules.

---

## 3. RESTful API Documentation

The system adheres strictly to REST architectural principles:
- **Stateless Communication**: No session cookies; all requests are authenticated via Bearer JWT or API Key.
- **Uniform Resource Identifiers (URIs)**: Plural noun naming conventions (`/events`, `/venues`, `/bookings`, `/users`).
- **Standard HTTP Methods**:
  - `GET`: Idempotent data retrieval.
  - `POST`: Creation of new resources.
  - `PUT`: Update or state transition of existing resources.
  - `DELETE`: Removal of resources.
- **Consistent JSON Responses & HTTP Status Codes**:
  - `200 OK` / `201 Created` for successful operations.
  - `400 Bad Request` for validation failures.
  - `401 Unauthorized` for invalid or missing credentials.
  - `403 Forbidden` for insufficient role privileges.
  - `404 Not Found` for nonexistent resources.
  - `429 Too Many Requests` for rate limit violations.

(For complete endpoint request/response payloads, see [API_DOCUMENTATION.md](file:///C:/xampp/htdocs/event_ticketing_system/API_DOCUMENTATION.md)).

---

## 4. API Testing

The API was validated through two rigorous testing methodologies:
1. **Automated Unit & Integration Test Suite** (`backend/test_api.py`):
   - 9 automated tests validating health, JWT authentication, API Key authorization, event filtering & search, venue listing, customer booking lifecycle (reservation -> external QR -> PDF download -> gate verification -> cancellation -> inventory release), and RBAC admin protections.
   - **Result**: 9 out of 9 tests passing (100% success rate in 5.89s).
2. **Postman Collection** (`postman/event_ticketing_postman_collection.json`):
   - Comprehensive collection containing pre-configured requests, environment variables (`{{baseUrl}}`, `{{token}}`, `{{apiKey}}`), and automated test assertions.

---

## 5. System Implementation

### 5.1 Shared Backend Implementation
- **Framework**: Python FastAPI (ASGI) with Starlette and Pydantic v2.
- **Database Driver**: PyMySQL with custom dictionary cursor and automatic type serialization for Decimal and Datetime types.
- **Modular Router Design**:
  - `backend/routers/auth_routes.py`: Registration, JWT issuance, profile inspection.
  - `backend/routers/users_routes.py`: Administrative user management and RBAC.
  - `backend/routers/venues_routes.py`: Venue registrations and approval workflows.
  - `backend/routers/events_routes.py`: Event publishing, category tagging, search & sorting.
  - `backend/routers/bookings_routes.py`: Ticket checkout, cancellation, external QR code generation, PDF generation, and gate validation.
  - `backend/routers/stats_routes.py`: Health telemetry and external API monitoring.

### 5.2 Frontend Implementation
- **Architecture**: Responsive Single Page Application (SPA) built using Bootstrap 5, FontAwesome/Bootstrap Icons, and Vanilla JavaScript (`app.js`).
- **Frontend-Backend Communication**:
  - Asynchronous AJAX `fetch` calls to `API_BASE` (`http://127.0.0.1:8000`).
  - Automatic JWT token attachment in `Authorization` headers.
  - Real-time DOM updates without page reloads (dynamic cards, modal dialogs, QR view, PDF download, and toast alerts).

---

## 6. System Demonstration

### 6.1 Demonstration Workflows
1. **XAMPP Control Center (`index.php`)**:
   - Accessing `http://localhost/event_ticketing_system/` in Apache displays server connection status, live record counts from MySQL, quick startup commands, and direct links to the Web Portal, Swagger UI, and ReDoc.
2. **Customer Ticket Booking Workflow**:
   - Customer logs in, explores upcoming events using search filters, clicks "Book Now", selects quantity and payment method.
   - System atomically reserves inventory, generates a unique ticket code (`TKT-XXXX`), and provides immediate access to live QR pass and PDF e-ticket.
3. **Gate Scanner Verification Workflow**:
   - Organiser or Admin inputs the attendee's ticket code at the venue gate scanner.
   - The API verifies ticket validity, prevents admission for cancelled tickets, and displays attendee details.

---

## 7. Project Repository

The complete repository structure:
```
event_ticketing_system/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── middleware.py
│   ├── external_services.py
│   ├── test_api.py
│   └── routers/
├── database/
│   ├── event_ticketing_db.sql
│   ├── ddl.sql
│   ├── dml.sql
│   └── erd_diagram.md
├── frontend/
│   ├── index.html
│   └── static/
├── postman/
│   └── event_ticketing_postman_collection.json
├── index.php
├── start_server.ps1
├── start_server.bat
├── API_DOCUMENTATION.md
├── DEBUGGING_AND_PERFORMANCE.md
├── PROJECT_REPORT.md
└── README.md
```

---

## 8. Additional & Advanced Features

1. **Dual-Layer Authentication (JWT + API Key)**:
   - Supports both user browser sessions (JWT) and headless microservice integrations (`X-API-Key`).
2. **IP Rate Limiting**:
   - Middleware tracking requests per minute per client IP to safeguard against denial-of-service and brute-force attacks.
3. **Genuine External QR Code & PDF APIs**:
   - Interacts via HTTP requests with `api.qrserver.com` and `quickchart.io` with automated failover and telemetry logging.
4. **Automated Inventory Balancing**:
   - Database transactions guarantee that cancelled bookings immediately restore available ticket stock.

---

## 9. Debugging and Performance Optimisation Summary

(Detailed in [DEBUGGING_AND_PERFORMANCE.md](file:///C:/xampp/htdocs/event_ticketing_system/DEBUGGING_AND_PERFORMANCE.md)):
- Resolved database column mismatches (`image_url`, `cancellation_reason`, `cancelled_at`).
- Implemented dual-provider failover for third-party QR code generation.
- Optimized query execution with pagination limits and indexed foreign keys, reducing response latencies by up to **74%**.

---

## 10. Individual Reflection and Contribution Record

### Student Contribution:
- **Responsibilities**: Designed the relational database schema (`ddl.sql`, `dml.sql`), implemented FastAPI RESTful endpoints with JWT & API Key authentication, developed middleware (logging, rate limiting, exception handling), integrated genuine external QR and PDF APIs, built the Single Page Application frontend, and authored the Postman collection and automated test suites.
- **Challenges Faced**: Resolving asynchronous database serialization with PyMySQL and configuring resilient failover for third-party cloud REST APIs during high network latency.
- **Solutions & Lessons Learned**: Gained deep practical mastery of REST architectural constraints, HTTP status code semantics, atomic database inventory locking, and stateless token-based authorization.
- **Future Improvements**: Adding WebSocket real-time live seat selection and integrating an SMS notification gateway.
