from datetime import datetime, timezone
from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    """Health check endpoint returning service status and timestamp."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elexon_upstream": settings.ELEXON_API_BASE_URL,
    }
