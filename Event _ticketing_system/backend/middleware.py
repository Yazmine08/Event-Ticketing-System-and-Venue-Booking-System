"""
Middleware and API Management Module
Implements:
1. Request Logging Middleware (with duration and status code)
2. Rate Limiting Middleware (Sliding Window per IP address)
3. Centralized Exception Handlers (400, 401, 403, 404, 422, 429, 500)
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api_management")

# In-Memory Rate Limiter Configuration: 120 requests per 60 seconds per IP
RATE_LIMIT_MAX_REQUESTS = 120
RATE_LIMIT_WINDOW_SECONDS = 60
client_request_history = defaultdict(list)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    API Management: Rate limiting middleware.
    Tracks client requests in a sliding window.
    Returns HTTP 429 Too Many Requests if client exceeds quota.
    """
    async def dispatch(self, request: Request, call_next):
        # Allow static files or documentation without strict limit
        client_ip = request.client.host if request.client else "127.0.0.1"
        current_time = time.time()
        
        # Cleanup requests older than window
        requests = client_request_history[client_ip]
        client_request_history[client_ip] = [ts for ts in requests if current_time - ts < RATE_LIMIT_WINDOW_SECONDS]
        
        remaining = max(0, RATE_LIMIT_MAX_REQUESTS - len(client_request_history[client_ip]))
        
        if len(client_request_history[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"[RateLimit] Client {client_ip} exceeded rate limit.")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "error": {
                        "code": 429,
                        "type": "RateLimitExceeded",
                        "message": "Too many requests. Please slow down.",
                        "details": f"Maximum allowed: {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds."
                    }
                },
                headers={
                    "Retry-After": str(RATE_LIMIT_WINDOW_SECONDS),
                    "X-RateLimit-Limit": str(RATE_LIMIT_MAX_REQUESTS),
                    "X-RateLimit-Remaining": "0"
                }
            )

        client_request_history[client_ip].append(current_time)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1 if remaining > 0 else 0)
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware: Request and response logging middleware.
    Logs HTTP method, URI path, status code, and execution time in milliseconds.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000.0
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        
        log_message = f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms) [IP: {client_ip}]"
        if response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        return response

def setup_exception_handlers(app):
    """
    Centralized error handling middleware.
    Provides consistent, standard JSON error envelopes for all errors and exceptions.
    """
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": {
                    "code": exc.status_code,
                    "type": "HTTPException",
                    "message": str(exc.detail),
                    "details": None
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        formatted_errors = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            formatted_errors.append({
                "field": loc,
                "message": error.get("msg"),
                "type": error.get("type")
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "error": {
                    "code": 422,
                    "type": "ValidationError",
                    "message": "Input validation failed. Please check the request parameters or body.",
                    "details": formatted_errors
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": {
                    "code": 500,
                    "type": "InternalServerError",
                    "message": "An unexpected server error occurred. Please contact the administrator.",
                    "details": str(exc)
                }
            }
        )
