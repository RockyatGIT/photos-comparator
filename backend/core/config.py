import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

class Settings:
    PROJECT_NAME: str = "Google Photos Comparator"
    VERSION: str = "2.0.0"

    # Filesystem Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    THUMBNAILS_DIR: Path = DATA_DIR / "thumbnails"
    DB_PATH: Path = DATA_DIR / "comparator.db"
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

    # Server Runtime Config
    HOST: str = os.getenv("HOST", "0.0.0.0").strip()
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # OAuth & Google APIs
    REDIRECT_URI: str = os.getenv("REDIRECT_URI", f"http://localhost:{PORT}/api/auth/callback").strip()
    AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_PHOTOS_MEDIA_URL: str = "https://photoslibrary.googleapis.com/v1/mediaItems"
    PICKER_API_BASE: str = "https://photospicker.googleapis.com/v1"

    # Google Cloud Console URLs
    GOOGLE_CONSOLE_PICKER_URL: str = "https://console.developers.google.com/apis/api/photospicker.googleapis.com/overview"
    GOOGLE_CONSOLE_LIBRARY_URL: str = "https://console.cloud.google.com/apis/library/photospicker.googleapis.com"
    GOOGLE_CONSOLE_CREDENTIALS_URL: str = "https://console.cloud.google.com/apis/credentials"

    SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/photospicker.mediaitems.readonly",
        "https://www.googleapis.com/auth/photoslibrary.readonly",
    ]

    # HTTP Client Timeouts (seconds)
    HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT", "30.0"))
    USERINFO_TIMEOUT: float = float(os.getenv("USERINFO_TIMEOUT", "15.0"))

    # Image Processing & Thumbnails
    THUMBNAIL_MAX_DIMENSION: int = int(os.getenv("THUMBNAIL_MAX_DIMENSION", "512"))
    THUMBNAIL_JPEG_QUALITY: int = int(os.getenv("THUMBNAIL_JPEG_QUALITY", "85"))
    UPLOAD_JPEG_QUALITY: int = int(os.getenv("UPLOAD_JPEG_QUALITY", "90"))
    DEFAULT_WIDTH: int = 1920
    DEFAULT_HEIGHT: int = 1080

    # API Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    PICKER_PAGE_SIZE: int = int(os.getenv("PICKER_PAGE_SIZE", "100"))
    MAX_GALLERY_LIMIT: int = int(os.getenv("MAX_GALLERY_LIMIT", "200"))

    # Matching & Perceptual Hashing
    MAX_HASH_BITS: int = 64
    DEFAULT_MATCH_DISTANCE: int = int(os.getenv("DEFAULT_MATCH_DISTANCE", "10"))
    EXACT_MATCH_DISTANCE: int = 0
    NEAR_DUPLICATE_DISTANCE: int = 4
    SIMILAR_MATCH_DISTANCE: int = 10

    # Token Lifecycles
    DEFAULT_TOKEN_EXPIRY_SECONDS: int = 3600
    TOKEN_REFRESH_BUFFER_SECONDS: int = 300  # 5 minutes buffer before expiry

    # Demo Dataset Defaults
    DEMO_ACCOUNT_1_EMAIL: str = os.getenv("DEMO_ACCOUNT_1_EMAIL", "demo.personal@example.com")
    DEMO_ACCOUNT_1_NAME: str = os.getenv("DEMO_ACCOUNT_1_NAME", "Demo User (Personal)")
    DEMO_ACCOUNT_2_EMAIL: str = os.getenv("DEMO_ACCOUNT_2_EMAIL", "demo.backup@example.com")
    DEMO_ACCOUNT_2_NAME: str = os.getenv("DEMO_ACCOUNT_2_NAME", "Demo User (Backup)")
    DEMO_AVATAR_BASE_URL: str = "https://api.dicebear.com/7.x/avataaars/svg"

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    def get_client_id(self) -> str:
        from ..repositories.settings_repo import SettingsRepository
        val = SettingsRepository.get("google_client_id")
        if val:
            return val.strip()
        return os.getenv("GOOGLE_CLIENT_ID", "").strip()

    def get_client_secret(self) -> str:
        from ..repositories.settings_repo import SettingsRepository
        val = SettingsRepository.get("google_client_secret")
        if val:
            return val.strip()
        return os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    def save_credentials(self, client_id: str, client_secret: str) -> None:
        from ..repositories.settings_repo import SettingsRepository
        SettingsRepository.set("google_client_id", client_id.strip())
        SettingsRepository.set("google_client_secret", client_secret.strip())

        # Also persist to .env
        env_content = f"""# Google Cloud OAuth 2.0 Credentials (Updated from Frontend)
GOOGLE_CLIENT_ID="{client_id.strip()}"
GOOGLE_CLIENT_SECRET="{client_secret.strip()}"
REDIRECT_URI="{self.REDIRECT_URI}"
"""
        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(env_content)
        except Exception as e:
            print(f"Warning: could not write to .env: {e}")

settings = Settings()
