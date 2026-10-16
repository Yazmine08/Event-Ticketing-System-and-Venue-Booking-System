"""
Main Application Entry Point
FastAPI RESTful API for Event Ticketing and Venue Booking System
Course: SWC3633 / SWC4443 Web API Development
Universiti Poly-Tech Malaysia (UPTM)
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

# Ensure root project directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.middleware import RateLimitingMiddleware, RequestLoggingMiddleware, setup_exception_handlers
from backend.routers import (
    auth_routes,
    users_routes,
    venues_routes,
    events_routes,
    bookings_routes,
    categories_routes,
    stats_routes
)

app = FastAPI(
    title="Event Ticketing & Venue Booking RESTful Web API",
    description=(
        "## SWC3633 / SWC4443 Web API Development Project\n\n"
        "A full-featured RESTful API developed for **Universiti Poly-Tech Malaysia (UPTM)** supporting:\n\n"
        "- **Core Resources**: `/users`, `/events`, `/venues`, `/bookings`, `/categories` with full CRUD operations\n"
        "- **Security**: JWT Bearer Authentication, API Key header protection (`X-API-Key`), and Role-Based Access Control (Admin, Organiser, Customer)\n"
        "- **Middleware**: Request logging, rate limiting (120 req/min), centralized JSON error handling\n"
        "- **API Management**: Dynamic pagination, filtering, full-text keyword search, and column sorting\n"
        "- **Third-Party API Integrations**:\n"
        "  1. **QR Code Generator API** (`api.qrserver.com` / `quickchart.io`)\n"
        "  2. **PDF Generation API** (Admission pass & payment invoice with embedded QR code)\n\n"
        "### Default Pre-Seeded Accounts (Password for all: `password123`)\n"
        "- **Admin**: `admin@example.com` (API Key: `adm_live_key_9876543210abcdef`)\n"
        "- **Organiser**: `aina@example.com` (API Key: `org_live_key_abcdef1234567890`)\n"
        "- **Organiser 2**: `daniel@example.com` (API Key: `org_live_key_daniel23456789`)\n"
        "- **Customer 1**: `sarah@example.com` (API Key: `cus_live_key_aaaabbbbccccdddd`)\n"
        "- **Customer 2**: `amir@example.com` (API Key: `cus_live_key_amir1122334455`)\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Custom Middlewares (Logging & Rate Limiting)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)

# 3. Centralized Exception Handlers
setup_exception_handlers(app)

# 4. Include Resource Routers (Mounted under both /api and root / for full REST compliance)
routers = [
    auth_routes.router,
    users_routes.router,
    venues_routes.router,
    events_routes.router,
    bookings_routes.router,
    categories_routes.router,
    stats_routes.router
]

for r in routers:
    app.include_router(r, prefix="/api")
    app.include_router(r, prefix="", include_in_schema=False)

# 5. Serve Frontend Static Assets
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the main single-page application frontend."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Event Ticketing REST API is running. Visit /docs for Swagger UI documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
