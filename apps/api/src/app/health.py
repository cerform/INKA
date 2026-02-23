from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.deps.auth import get_db
from app.settings import settings

router = APIRouter()
probe_router = APIRouter()

@router.get("/")
@probe_router.get("/healthz")
async def health_check():
    trace_id = None
    try:
        from packages.observability import get_current_trace_id
        trace_id = get_current_trace_id()
    except Exception:
        pass
    return {"status": "ok", "trace_id": trace_id}

@router.get("/ready")
@probe_router.get("/readyz")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        # Check DB connectivity
        db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unready", "db": "disconnected", "error": str(e)}
        )

@router.get("/version")
@probe_router.get("/version")
async def version_check():
    return {
        "service": settings.project_name,
        "version": settings.version,
        "env": settings.env
    }
