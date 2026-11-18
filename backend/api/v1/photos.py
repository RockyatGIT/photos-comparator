from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends, File, UploadFile
from fastapi.responses import FileResponse

from ...core.config import settings
from ...services.photos_service import PhotosService
from ...services.demo_service import DemoService
from ...services.matching_service import MatchingService
from ...schemas.photo import PhotoListResponse, DateBoundsResponse, PickerStartResponse, PickerPollResponse, UploadResponse
from ..deps import get_photos_service, get_demo_service, get_matching_service

router = APIRouter(prefix="/photos", tags=["Photos"])

@router.get("", response_model=PhotoListResponse)
def list_photos(
    account: int = Query(..., ge=1, le=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = settings.MAX_GALLERY_LIMIT,
    offset: int = 0,
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Lists photos for an account with optional date range filtering."""
    photos = photos_srv.get_photos(account, start_date=start_date, end_date=end_date, limit=limit, offset=offset)
    return {
        "account_id": account,
        "photos": photos,
        "total": len(photos),
        "start_date": start_date,
        "end_date": end_date
    }

@router.get("/date-bounds", response_model=DateBoundsResponse)
def get_date_bounds(photos_srv: PhotosService = Depends(get_photos_service)):
    """Retrieves the earliest and latest photo capture dates in the library."""
    return photos_srv.get_date_bounds()

@router.get("/thumbnail/{filename}")
def get_thumbnail(filename: str):
    """Serves cached local thumbnail images."""
    file_path = settings.THUMBNAILS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(file_path, media_type="image/jpeg")

@router.post("/picker/start", response_model=PickerStartResponse)
async def picker_start(
    account: int = Query(..., ge=1, le=2),
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Initializes a Google Photos Picker API session for photo selection."""
    try:
        session_info = await photos_srv.create_picker_session(account)
        return session_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Google Photos Picker session: {str(e)}")

@router.post("/picker/poll", response_model=PickerPollResponse)
async def picker_poll(
    account: int = Query(..., ge=1, le=2),
    session_id: str = Query(...),
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Polls picker session to check if user completed photo selection."""
    try:
        result = await photos_srv.poll_and_fetch_picker_photos(account, session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking picker session: {str(e)}")

@router.post("/upload", response_model=UploadResponse)
async def upload_photos(
    account: int = Query(..., ge=1, le=2),
    files: List[UploadFile] = File(...),
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Uploads local photo files directly into an account."""
    saved = []
    for file in files:
        content = await file.read()
        res = photos_srv.save_uploaded_photo(account, file.filename, content)
        saved.append(res)
    return {"status": "success", "uploaded_count": len(saved)}

@router.post("/sync")
async def sync_photos(
    account: int = Query(..., ge=1, le=2),
    photos_srv: PhotosService = Depends(get_photos_service)
):
    """Syncs photos using Google Photos Library API (fallback/legacy)."""
    try:
        photos = await photos_srv.fetch_photos_from_google(account, page_size=settings.LIBRARY_PAGE_SIZE)
        return {"status": "success", "synced_photos": len(photos)}
    except Exception as e:
        err_msg = str(e)
        if "403" in err_msg or "PERMISSION_DENIED" in err_msg:
            raise HTTPException(
                status_code=403,
                detail="Google retired legacy photoslibrary.readonly in 2025. Please use the 'Pick Photos' button to select photos via the modern Google Photos Picker API!"
            )
        raise HTTPException(status_code=500, detail=err_msg)

@router.post("/demo-sync")
def demo_sync(
    demo_srv: DemoService = Depends(get_demo_service),
    matcher_srv: MatchingService = Depends(get_matching_service)
):
    """Loads realistic sample photos with known duplicate, burst, and unique pairs."""
    result = demo_srv.seed_demo_data()
    matches_result = matcher_srv.compute_matches()
    return {
        "status": "success",
        "message": "Loaded sample photos for both accounts and ran similarity matching",
        "photos": result,
        "matches": matches_result
    }
