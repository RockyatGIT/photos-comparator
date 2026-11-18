# Backward compatibility alias - proxies to backend.core.database and repositories
from .core.database import get_db_connection, init_db
from .repositories.account_repo import AccountRepository
from .repositories.photo_repo import PhotoRepository
from .repositories.match_repo import MatchRepository
from .repositories.settings_repo import SettingsRepository

def get_connection():
    import sqlite3
    from .core.config import settings
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

get_setting = SettingsRepository.get
set_setting = SettingsRepository.set

save_account_token = AccountRepository.save_token
get_account = AccountRepository.get
get_all_accounts = AccountRepository.get_all
remove_account = AccountRepository.remove

save_photos = PhotoRepository.save_photos
update_photo_hashes = PhotoRepository.update_photo_hashes
get_photos = PhotoRepository.get_photos
get_photos_for_matching = PhotoRepository.get_photos_for_matching
get_unique_photos = PhotoRepository.get_unique_photos
get_date_bounds = PhotoRepository.get_date_bounds

save_matches = MatchRepository.save_matches
get_matches = MatchRepository.get_matches
