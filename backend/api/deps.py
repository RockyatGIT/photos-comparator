from ..services.auth_service import AuthService, auth_service
from ..services.photos_service import PhotosService, photos_service
from ..services.matching_service import MatchingService, matching_service
from ..services.demo_service import DemoService, demo_service
from ..repositories.account_repo import AccountRepository
from ..repositories.photo_repo import PhotoRepository
from ..repositories.match_repo import MatchRepository
from ..repositories.settings_repo import SettingsRepository

def get_auth_service() -> AuthService:
    return auth_service

def get_photos_service() -> PhotosService:
    return photos_service

def get_matching_service() -> MatchingService:
    return matching_service

def get_demo_service() -> DemoService:
    return demo_service

def get_account_repo() -> AccountRepository:
    return AccountRepository

def get_photo_repo() -> PhotoRepository:
    return PhotoRepository

def get_match_repo() -> MatchRepository:
    return MatchRepository

def get_settings_repo() -> SettingsRepository:
    return SettingsRepository
