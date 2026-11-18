from fastapi import APIRouter, Depends
from ...core.config import settings
from ...repositories.account_repo import AccountRepository
from ...repositories.photo_repo import PhotoRepository
from ...repositories.match_repo import MatchRepository
from ...schemas.account import SystemStatusResponse
from ..deps import get_account_repo, get_photo_repo, get_match_repo

router = APIRouter(tags=["Status"])

@router.get("/status", response_model=SystemStatusResponse)
def get_status(
    account_repo: AccountRepository = Depends(get_account_repo),
    photo_repo: PhotoRepository = Depends(get_photo_repo),
    match_repo: MatchRepository = Depends(get_match_repo)
):
    """Returns high-level status of both accounts, total photos, matches, and OAuth setup."""
    acc1 = account_repo.get(1)
    acc2 = account_repo.get(2)
    p1_count = photo_repo.count(1)
    p2_count = photo_repo.count(2)
    matches_count = match_repo.count()

    has_credentials = bool(settings.get_client_id() and settings.get_client_secret())

    return {
        "google_credentials_configured": has_credentials,
        "redirect_uri": settings.REDIRECT_URI,
        "accounts": {
            "account_1": {
                "connected": acc1 is not None,
                "email": acc1["email"] if acc1 else None,
                "name": acc1["name"] if acc1 else None,
                "picture": acc1["picture"] if acc1 else None,
                "photo_count": p1_count
            },
            "account_2": {
                "connected": acc2 is not None,
                "email": acc2["email"] if acc2 else None,
                "name": acc2["name"] if acc2 else None,
                "picture": acc2["picture"] if acc2 else None,
                "photo_count": p2_count
            }
        },
        "total_matches": matches_count
    }
