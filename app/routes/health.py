"""Health check endpoint controller.

Rule 1.2: Endpoints follow standard base paths.
"""

from fastapi import APIRouter
from app.schemas.domain import HealthResponse
from app.utils.logger import log_info

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns application status, service identification, and current version.

    Returns:
        HealthResponse: Health status payload.
    """
    log_info("get_health", "Health check endpoint invoked")
    return HealthResponse(status="ok", service="tourism-portal-api", version="0.1.0")
