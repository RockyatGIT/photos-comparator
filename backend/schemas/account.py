from typing import Optional, Dict
from pydantic import BaseModel

class AccountStatus(BaseModel):
    connected: bool
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    photo_count: int = 0

class SystemStatusResponse(BaseModel):
    google_credentials_configured: bool
    redirect_uri: str
    accounts: Dict[str, AccountStatus]
    total_matches: int
