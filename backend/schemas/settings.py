from pydantic import BaseModel

class CredentialsPayload(BaseModel):
    client_id: str
    client_secret: str

class CredentialsStatusResponse(BaseModel):
    client_id: str
    is_configured: bool
    has_secret: bool
    redirect_uri: str

class CredentialsUpdateResponse(BaseModel):
    status: str
    message: str
    client_id: str
    is_configured: bool
