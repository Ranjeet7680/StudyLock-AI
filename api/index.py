"""
StudyLock AI - Vercel Serverless Function Entrypoint
Ref: StudyLock AI Architecture Specification Section 5, 13, 24.1
"""
import sys
import os

# Ensure repository root and services/api are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_API_DIR = os.path.join(BASE_DIR, "services", "api")

for p in (BASE_DIR, SERVICES_API_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Set database path to /tmp for Vercel / Lambda environment if not set
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:////tmp/studylock.db"

try:
    from services.api.app.main import app
except Exception as e:
    import traceback
    traceback.print_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="StudyLock AI (Degraded Mode)")
    @app.get("/health")
    @app.get("/api/v1/health")
    def health_fallback():
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
