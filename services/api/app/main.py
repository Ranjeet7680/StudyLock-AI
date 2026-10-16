"""
StudyLock AI - FastAPI Modular Monolith API
Ref: StudyLock AI Architecture Specification Section 5, 13, 24.1
"""
import uuid
import time
import sys
import os

# Ensure services/api directory and repo root are in sys.path
api_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(api_root)
for p in (api_root, repo_root):
    if p and p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .database import engine, Base
from .core.errors import StudyLockException, studylock_exception_handler
from .routers import (
    auth,
    users,
    devices,
    tasks,
    schedules,
    sessions,
    block_rules,
    rewards,
    analytics,
    sync,
    privacy,
    video,
)

# Auto-create tables on startup (works with both SQLite and Postgres)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[StudyLock API] Warning initializing DB tables: {e}")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Cross-platform focus engine, blocking adapters, tasks, schedules, and rewards ledger API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows browser extension and dashboard access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    response.headers["X-Request-ID"] = request_id
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Register Exception Handlers (Spec Section 13.4)
app.add_exception_handler(StudyLockException, studylock_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        error_messages.append(f"{loc}: {err.get('msg')}")

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed: " + "; ".join(error_messages),
                "request_id": request_id,
                "retryable": False
            }
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "StudyLock AI API",
        "version": settings.API_VERSION,
        "environment": settings.APP_ENV
    }


@app.get("/", include_in_schema=False)
async def root_endpoint():
    for cand in [
        os.path.join(api_root, "public", "index.html"),
        os.path.join(repo_root, "public", "index.html"),
        os.path.join(repo_root, "apps", "web", "index.html"),
        os.path.join(os.getcwd(), "public", "index.html")
    ]:
        if os.path.isfile(cand):
            return FileResponse(cand, media_type="text/html")
    return {
        "service": "StudyLock AI API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }


@app.get("/style.css", include_in_schema=False)
async def serve_css():
    for cand in [
        os.path.join(api_root, "public", "style.css"),
        os.path.join(repo_root, "public", "style.css"),
        os.path.join(repo_root, "apps", "web", "style.css"),
        os.path.join(os.getcwd(), "public", "style.css")
    ]:
        if os.path.isfile(cand):
            return FileResponse(cand, media_type="text/css")
    return JSONResponse(status_code=404, content={"error": "Not Found"})


@app.get("/app.js", include_in_schema=False)
async def serve_js():
    for cand in [
        os.path.join(api_root, "public", "app.js"),
        os.path.join(repo_root, "public", "app.js"),
        os.path.join(repo_root, "apps", "web", "app.js"),
        os.path.join(os.getcwd(), "public", "app.js")
    ]:
        if os.path.isfile(cand):
            return FileResponse(cand, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"error": "Not Found"})


@app.get("/favicon.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    for cand in [
        os.path.join(api_root, "public", "favicon.svg"),
        os.path.join(repo_root, "public", "favicon.svg"),
        os.path.join(repo_root, "apps", "web", "favicon.svg"),
        os.path.join(os.getcwd(), "public", "favicon.svg")
    ]:
        if os.path.isfile(cand):
            return FileResponse(cand, media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"error": "Not Found"})


# Include Routers with /api/v1 prefix (Spec Section 13.1)
API_V1_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)
app.include_router(devices.router, prefix=API_V1_PREFIX)
app.include_router(tasks.router, prefix=API_V1_PREFIX)
app.include_router(schedules.router, prefix=API_V1_PREFIX)
app.include_router(sessions.router, prefix=API_V1_PREFIX)
app.include_router(block_rules.router, prefix=API_V1_PREFIX)
app.include_router(rewards.router, prefix=API_V1_PREFIX)
app.include_router(analytics.router, prefix=API_V1_PREFIX)
app.include_router(sync.router, prefix=API_V1_PREFIX)
app.include_router(privacy.router, prefix=API_V1_PREFIX)
app.include_router(video.router, prefix=API_V1_PREFIX)

