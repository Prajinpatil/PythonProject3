"""
Surveillance Intelligence System - Main Application
FastAPI backend for real-time threat detection and analytics
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.db import init_db, close_db, get_db_context, check_db_health
from app.database.init_data import initialize_demo_data
from app.api.routes import auth
from app.threat_detection.routes import router as threat_router


# =========================
# LOGGING CONFIGURATION
# =========================
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


# =========================
# APPLICATION LIFECYCLE
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Surveillance Intelligence System")
    try:
        await init_db()
        if settings.ENVIRONMENT == "development":
            async with get_db_context() as db:
                await initialize_demo_data(db)
        logger.info("System startup complete")
    except Exception:
        logger.exception("Startup failed")
        raise
    yield
    logger.info("Shutting down system")
    await close_db()
    logger.info("Shutdown complete")


# =========================
# APPLICATION INSTANCE
# =========================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time surveillance intelligence with explainable threat scoring",
    lifespan=lifespan,
    docs_url=settings.DOCS_URL if settings.DOCS_ENABLED else None,
    redoc_url=settings.REDOC_URL if settings.DOCS_ENABLED else None,
    openapi_url=settings.OPENAPI_URL if settings.DOCS_ENABLED else None,
)


# =========================
# MIDDLEWARE
# =========================

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# 2. Request logger
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "%s %s - %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    return response


# 3. Security headers — skipped for /static/* so CSS/JS load correctly
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    skip_prefixes = ("/docs", "/redoc", "/openapi.json", "/static")
    if any(request.url.path.startswith(p) for p in skip_prefixes):
        return response
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' https://cdn.jsdelivr.net; "
        "media-src 'self' blob:; "
        "worker-src blob:; "
    )
    return response


# =========================
# EXCEPTION HANDLERS
# =========================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": repr(exc) if settings.DEBUG else "An error occurred",
            "path": request.url.path,
        },
    )


# =========================
# ROUTERS
# =========================
app.include_router(auth.router, prefix="/api/v1")
app.include_router(threat_router, prefix="/threat", tags=["Threat Detection"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =========================
# PAGE ROUTES
# =========================
@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))

@app.get("/dashboard")
async def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))

@app.get("/cameras")
async def cameras():
    return FileResponse(os.path.join(STATIC_DIR, "cameras.html"))

@app.get("/events")
async def events():
    return FileResponse(os.path.join(STATIC_DIR, "events.html"))

@app.get("/analytics")
async def analytics():
    return FileResponse(os.path.join(STATIC_DIR, "analytics.html"))


# =========================
# API ROUTES
# =========================
@app.get("/health")
async def health_check():
    healthy = await check_db_health()
    return {
        "status": "healthy" if healthy else "degraded",
        "database": "connected" if healthy else "disconnected",
        "timestamp": time.time(),
    }

@app.get("/api/v1/info")
async def api_info():
    return {
        "version": "1.0.0",
        "features": [
            "Real-time threat detection",
            "Multi-factor threat scoring",
            "Pattern detection",
            "Analytics engine",
            "Alert management",
            "Role-based access control",
        ],
        "supported_objects": [
            "human", "vehicle", "animal", "drone",
            "weapon", "bag", "package",
        ],
    }

@app.get("/debug-path")
async def debug_path():
    return {
        "BASE_DIR": BASE_DIR,
        "STATIC_DIR": STATIC_DIR,
        "static_exists": os.path.exists(STATIC_DIR),
        "files": os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else "NOT FOUND"
    }


# =========================
# DEBUG ONLY
# =========================
if settings.DEBUG:
    @app.get("/debug/config")
    async def debug_config():
        return {
            "environment": settings.ENVIRONMENT,
            "database_url": settings.DATABASE_URL,
            "cors_origins": settings.CORS_ORIGINS,
            "jwt_expires_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "rate_limit": settings.RATE_LIMIT_PER_MINUTE,
        }


# =========================
# STATIC FILES — must be LAST
# =========================
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )