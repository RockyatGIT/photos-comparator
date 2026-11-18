from fastapi import APIRouter
from .auth import router as auth_router
from .photos import router as photos_router
from .matcher import router as matcher_router
from .settings import router as settings_router
from .status import router as status_router

api_router = APIRouter(prefix="/api")

api_router.include_router(status_router)
api_router.include_router(auth_router)
api_router.include_router(photos_router)
api_router.include_router(matcher_router)
api_router.include_router(settings_router)
