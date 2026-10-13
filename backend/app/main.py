from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.init_db import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables upon startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API service for authentic scholarship intelligence and discovery.",
    lifespan=lifespan,
)

# Configure CORS for local development & dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def root_info():
    """Root metadata endpoint."""
    return {
        "message": "Welcome to Scholarship Intelligence Crawler API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
