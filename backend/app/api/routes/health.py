from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        app="RupeeRadar API",
        version="0.1.0",
        database="connected"
    )
