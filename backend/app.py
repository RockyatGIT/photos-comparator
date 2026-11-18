from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1.api import api_router

def create_app() -> FastAPI:
    """FastAPI Application Factory following industry standards."""
    app_instance = FastAPI(
        title=settings.PROJECT_NAME,
        description="High-performance dual-account Google Photos comparison and duplicate detection engine.",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS configuration
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app_instance.include_router(api_router)

    # Mount static frontend files
    if settings.FRONTEND_DIR.exists():
        app_instance.mount("/", StaticFiles(directory=str(settings.FRONTEND_DIR), html=True), name="frontend")

    return app_instance

app = create_app()
