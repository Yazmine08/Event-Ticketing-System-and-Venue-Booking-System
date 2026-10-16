# Event Ticketing & Venue Booking RESTful Web API System
**Course**: SWC3633 / SWC4443 Web API Development  
**Institution**: Universiti Poly-Tech Malaysia (UPTM)  
**Location**: `C:\xampp\htdocs\event_ticketing_system`  

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **XAMPP** (Apache & MySQL running on standard ports 80 and 3306)
- **Python 3.10+** (with `fastapi`, `uvicorn`, `pymysql`, `requests`, `pyjwt`, `bcrypt`, `reportlab`)

### 2. Database Setup (MySQL `event_ticketing_db`)
The MySQL database is configured and populated directly from `event_ticketing_db.sql`.
To re-import or reset the database at any time, run:
```powershell
python database/prepare_mysql_db.py
```
Or import `database/event_ticketing_db.sql` via **phpMyAdmin** (`http://localhost/phpmyadmin`).

### 3. Running the Server via PowerShell
Navigate to the project folder inside `C:\xampp\htdocs\event_ticketing_system`:
```powershell
cd C:\xampp\htdocs\event_ticketing_system
.\start_server.ps1
```
Or run directly:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Alternatively, double-click `start_server.bat` in Windows Explorer.

### 4. Accessing the System
Once started, you can access the system through either:
- **XAMPP Localhost Hub**: [http://localhost/event_ticketing_system](http://localhost/event_ticketing_system)
- **Direct Web Portal**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI / Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Specifications**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Running the Automated Test Suite
Run the 9 automated integration and unit tests:
```powershell
python backend/test_api.py
```

---

## 👥 Default Demo Accounts (Pre-Seeded)

The web application features a **"⚡ Quick Demo Switch"** dropdown in the top navbar for 1-click test persona switching without manual typing:

| Role | Name | Email | Password | Default API Key (`X-API-Key`) |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | Admin EventHub | `admin@example.com` | `password123` | `adm_live_key_9876543210abcdef` |
| **Organiser** | Aina Rahman | `aina@example.com` | `password123` | `org_live_key_abcdef1234567890` |
| **Organiser** | Daniel Lee | `daniel@example.com` | `password123` | `org_live_key_daniel23456789` |
| **Customer** | Sarah Ahmad | `sarah@example.com` | `password123` | `cus_live_key_aaaabbbbccccdddd` |
| **Customer** | Amir Hakim | `amir@example.com` | `password123` | `cus_live_key_amir1122334455` |

---

## 🌐 Genuine External Third-Party APIs

In strict compliance with the requirement (*"A locally installed library or package does not count as an external API service"*), this project communicates via HTTP with genuine external cloud REST APIs:

1. **QR Code Generator API**:
   - Primary: `https://api.qrserver.com/v1/create-qr-code/`
   - Secondary Fallback: `https://quickchart.io/qr`
   - Endpoint: `GET /api/bookings/{id}/qrcode` returns live external QR PNG image or metadata.
   - Interactive Live Testbench is available in the **"External APIs & Monitor"** tab.

2. **PDF Generation API Engine**:
   - Renders official PDF tickets with event branding, venue details, payment receipt, and the embedded live external QR code.
   - Endpoint: `GET /api/bookings/{id}/pdf` returns the binary PDF download.

3. **External API Telemetry & Audit Trail**:
   - Every external HTTP call records timestamp, service name, HTTP method, latency (ms), status code, and payload size.
   - Accessible via `GET /api/stats/external-apis` and displayed in real-time in the Admin Dashboard.

---

## 📁 Repository Structure
```
C:\xampp\htdocs\event_ticketing_system/
├── backend/
│   ├── main.py                     # FastAPI application entry point & router mounting
│   ├── database.py                 # MySQL PyMySQL connection & JSON serialization
│   ├── auth.py                     # JWT Bearer, Bcrypt, API Key & RBAC
│   ├── models.py                   # Pydantic validation schemas with flexible aliases
│   ├── middleware.py               # Rate limiting & request logging
│   ├── external_services.py        # External QR & PDF API integrations
│   ├── test_api.py                 # Automated test suite (9 test cases)
│   └── routers/
│       ├── auth_routes.py          # /auth & /api/auth (login, register, me)
│       ├── users_routes.py         # /users & /api/users (CRUD, RBAC)
│       ├── venues_routes.py        # /venues & /api/venues (CRUD, capacity check)
│       ├── events_routes.py        # /events & /api/events (CRUD, search, filters)
│       ├── bookings_routes.py      # /bookings & /api/bookings (Checkout, QR, PDF, gate check-in)
│       ├── categories_routes.py    # /categories & /api/categories
│       └── stats_routes.py         # /stats & /api/stats (Health & telemetry)
├── database/
│   ├── event_ticketing_db.sql      # Cleaned MySQL script ready for phpMyAdmin/MySQL
│   ├── ddl.sql                     # Data Definition Language script
│   ├── dml.sql                     # Data Manipulation Language script (5 records/table)
│   ├── prepare_mysql_db.py         # Automated database import & bcrypt hasher script
│   └── erd_diagram.md              # Entity Relationship Diagram & documentation
├── frontend/
│   ├── index.html                  # Full Single Page Web Application
│   └── static/
│       ├── css/app.css             # Responsive styling & themes
│       └── js/app.js               # Dynamic REST API client logic
├── postman/
│   └── event_ticketing_postman_collection.json  # Comprehensive Postman test collection
├── index.php                       # XAMPP Apache entry point & server health hub
├── start_server.bat                # 1-click Windows batch startup script
├── start_server.ps1                # PowerShell startup script
├── API_DOCUMENTATION.md            # Complete RESTful API documentation
├── DEBUGGING_AND_PERFORMANCE.md    # Issues, root causes, solutions, benchmarks
└── README.md                       # Setup and execution guide
```
