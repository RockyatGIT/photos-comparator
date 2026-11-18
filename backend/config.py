# Backward compatibility alias - proxies to backend.core.config
from .core.config import (
    settings,
    BASE_DIR,
    ENV_FILE,
    DATA_DIR,
    DB_PATH,
    THUMBNAILS_DIR,
    REDIRECT_URI,
    SCOPES,
)

def get_client_id() -> str:
    return settings.get_client_id()

def get_client_secret() -> str:
    return settings.get_client_secret()

def save_credentials(client_id: str, client_secret: str) -> None:
    settings.save_credentials(client_id, client_secret)

GOOGLE_CLIENT_ID = get_client_id()
GOOGLE_CLIENT_SECRET = get_client_secret()
