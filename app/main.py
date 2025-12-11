"""
Main FastAPI application entry point.
Configures the application, middleware, and routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import db_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application...")
    try:
        await db_manager.connect()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await db_manager.disconnect()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-tenant organization management service with JWT authentication",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service is running.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# TODO: Include routers here when implemented
# from app.routers import organization, admin
# app.include_router(organization.router, prefix="/org", tags=["Organizations"])
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
