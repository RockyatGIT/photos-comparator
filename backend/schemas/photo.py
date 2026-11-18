from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class PhotoDTO(BaseModel):
    id: Optional[int] = None
    account_id: int
    google_id: str
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    base_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    creation_time: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    phash: Optional[str] = None
    dhash: Optional[str] = None
    ahash: Optional[str] = None

class PhotoListResponse(BaseModel):
    account_id: int
    photos: List[Dict[str, Any]]
    total: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DateBoundsResponse(BaseModel):
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    total_photos: int = 0

class PickerStartResponse(BaseModel):
    session_id: str
    picker_uri: str

class PickerPollResponse(BaseModel):
    status: str
    ready: bool
    photos_count: int

class UploadResponse(BaseModel):
    status: str
    uploaded_count: int
