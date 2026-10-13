from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.schemas import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
def get_health(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Health check endpoint to verify backend service and database status."""
    db_status = "connected"
    try:
        # Check database connectivity with simple ping query
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    overall_status = "ok" if db_status == "connected" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
