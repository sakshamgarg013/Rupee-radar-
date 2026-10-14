from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.insights import router as insights_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(upload_router)
api_router.include_router(transactions_router)
api_router.include_router(analytics_router)
api_router.include_router(insights_router)
