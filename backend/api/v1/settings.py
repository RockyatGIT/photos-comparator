from fastapi import APIRouter, HTTPException
from ...core.config import settings
from ...schemas.settings import CredentialsPayload, CredentialsStatusResponse, CredentialsUpdateResponse

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/credentials", response_model=CredentialsStatusResponse)
def get_credentials():
    """Returns the current Google OAuth credentials configuration status."""
    cid = settings.get_client_id()
    csecret = settings.get_client_secret()
    return {
        "client_id": cid,
        "is_configured": bool(cid and csecret),
        "has_secret": bool(csecret),
        "redirect_uri": settings.REDIRECT_URI
    }

@router.post("/credentials", response_model=CredentialsUpdateResponse)
def update_credentials(payload: CredentialsPayload):
    """Updates and persists Google OAuth client credentials."""
    cid = payload.client_id.strip()
    csec = payload.client_secret.strip()
    if not cid or not csec:
        raise HTTPException(status_code=400, detail="Both Client ID and Client Secret are required.")

    settings.save_credentials(cid, csec)
    return {
        "status": "success",
        "message": "Google Cloud OAuth credentials saved successfully!",
        "client_id": cid,
        "is_configured": True
    }
