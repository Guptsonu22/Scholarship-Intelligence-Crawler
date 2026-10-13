from .health import router as health_router
from .discovery import router as discovery_router
from .crawl import router as crawl_router
from .scholarships import router as scholarships_router
from .extraction import router as extraction_router

__all__ = [
    "health_router",
    "discovery_router",
    "crawl_router",
    "scholarships_router",
    "extraction_router",
]
