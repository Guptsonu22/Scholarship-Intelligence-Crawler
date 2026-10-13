from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.crawl import router as crawl_router
from app.api.routes.scholarships import router as scholarships_router
from app.api.routes.extraction import router as extraction_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="")
api_router.include_router(discovery_router, prefix="")
api_router.include_router(crawl_router, prefix="")
api_router.include_router(scholarships_router, prefix="")
api_router.include_router(extraction_router, prefix="")

__all__ = ["api_router"]
