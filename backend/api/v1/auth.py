from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse
from ...core.config import settings
from ...services.auth_service import AuthService
from ...services.photos_service import PhotosService
from ..deps import get_auth_service, get_photos_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/url")
def auth_url(
    account: int = Query(..., ge=1, le=2),
    auth_srv: AuthService = Depends(get_auth_service)
):
    """Generates the Google OAuth 2.0 authorization URL for Account 1 or Account 2."""
    try:
        url = auth_srv.get_auth_url(account)
        return {"auth_url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/callback")
async def auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    auth_srv: AuthService = Depends(get_auth_service),
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Handles OAuth 2.0 redirect callback from Google, exchanges code for tokens, and redirects back to frontend."""
    try:
        account_id = int(state.replace("account_", ""))
    except Exception:
        account_id = 1

    try:
        await auth_srv.exchange_code_for_token(code, account_id)
        # Attempt initial sync with Library API (if items were previously created by app)
        try:
            await photos_srv.fetch_photos_from_google(account_id, page_size=settings.LIBRARY_PAGE_SIZE)
        except Exception as sync_err:
            print(f"Library API sync note: {sync_err}")
        return RedirectResponse(url=f"/?auth_success=true&account={account_id}")
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"/?auth_error={str(e)}")

@router.post("/disconnect")
def disconnect_account(
    account: int = Query(..., ge=1, le=2),
    auth_srv: AuthService = Depends(get_auth_service)
):
    """Disconnects the specified Google account and removes its cached photos."""
    auth_srv.disconnect(account)
    return {"status": "success", "message": f"Account {account} disconnected"}
