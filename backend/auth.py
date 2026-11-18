# Backward compatibility alias - proxies to backend.services.auth_service
from .services.auth_service import auth_service

get_auth_url = auth_service.get_auth_url
exchange_code_for_token = auth_service.exchange_code_for_token
get_valid_token = auth_service.get_valid_token
refresh_access_token = auth_service.refresh_access_token
fetch_user_info = auth_service.fetch_user_info
