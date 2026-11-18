# Backward compatibility alias - proxies to backend.services.matching_service
from .services.matching_service import matching_service

compute_matches = matching_service.compute_matches
get_matches = matching_service.get_matches
get_unique_photos = matching_service.get_unique_photos
parse_iso = matching_service.parse_iso
