import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from PIL import Image
import imagehash

from ..core.config import settings
from ..repositories.account_repo import AccountRepository
from ..repositories.photo_repo import PhotoRepository
from .auth_service import auth_service

class PhotosService:
    def __init__(
        self,
        photo_repo: PhotoRepository = PhotoRepository,
        account_repo: AccountRepository = AccountRepository
    ):
        self.photo_repo = photo_repo
        self.account_repo = account_repo

    async def create_picker_session(self, account_id: int) -> Dict[str, Any]:
        token = await auth_service.get_valid_token(account_id)
        if not token:
            raise ValueError(f"Account {account_id} is not authenticated")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            try:
                res = await client.post(f"{settings.PICKER_API_BASE}/sessions", headers=headers, json={})
                res.raise_for_status()
            except httpx.HTTPStatusError as e:
                try:
                    err_data = e.response.json()
                    msg = err_data.get("error", {}).get("message", "")
                    if "SERVICE_DISABLED" in str(err_data) or "has not been used in project" in msg:
                        project_num = settings.get_client_id().split("-")[0]
                        activation_url = f"{settings.GOOGLE_CONSOLE_PICKER_URL}?project={project_num}"
                        raise ValueError(f"Google Photos Picker API is disabled in your project. Click to enable it: {activation_url}")
                    raise ValueError(msg or str(e))
                except ValueError:
                    raise
                except Exception:
                    raise ValueError(str(e))

            data = res.json()
            raw_picker_uri = data["pickerUri"].rstrip("/")
            # Append /autoclose before query parameters
            picker_uri = f"{raw_picker_uri}/autoclose"

            account = self.account_repo.get(account_id)
            if account and account.get("email"):
                picker_uri = f"{picker_uri}?authuser={account['email']}"

            return {
                "session_id": data["id"],
                "picker_uri": picker_uri
            }

    async def poll_and_fetch_picker_photos(self, account_id: int, session_id: str) -> Dict[str, Any]:
        token = await auth_service.get_valid_token(account_id)
        if not token:
            raise ValueError(f"Account {account_id} is not authenticated")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            check_res = await client.get(f"{settings.PICKER_API_BASE}/sessions/{session_id}", headers=headers)
            check_res.raise_for_status()
            session_data = check_res.json()

            if not session_data.get("mediaItemsSet", False):
                return {"status": "waiting", "ready": False, "photos_count": 0}

            items_res = await client.get(
                f"{settings.PICKER_API_BASE}/mediaItems?sessionId={session_id}&pageSize={settings.PICKER_PAGE_SIZE}",
                headers=headers
            )
            items_res.raise_for_status()
            items_data = items_res.json()
            raw_items = items_data.get("mediaItems", [])

            photos_to_save = []
            for item in raw_items:
                media_file = item.get("mediaFile", {})
                metadata = item.get("mediaMetadata", {})
                photo_info = metadata.get("photo", {})

                base_url = media_file.get("baseUrl") or item.get("baseUrl") or ""
                filename = media_file.get("filename") or item.get("filename") or f"photo_{item['id'][:10]}.jpg"
                mime_type = media_file.get("mimeType") or item.get("mimeType") or item.get("type", "image/jpeg")
                creation_time = item.get("createTime") or metadata.get("creationTime") or datetime.now(timezone.utc).isoformat()

                photos_to_save.append({
                    "account_id": account_id,
                    "google_id": item["id"],
                    "filename": filename,
                    "mime_type": mime_type,
                    "base_url": base_url,
                    "creation_time": creation_time,
                    "width": metadata.get("width", settings.DEFAULT_WIDTH),
                    "height": metadata.get("height", settings.DEFAULT_HEIGHT),
                    "camera_make": photo_info.get("cameraMake"),
                    "camera_model": photo_info.get("cameraModel"),
                })

            self.photo_repo.save_photos(photos_to_save)
            await self.process_thumbnails_and_hashes(photos_to_save, token=token)

            # Clean up picker session
            try:
                await client.delete(f"{settings.PICKER_API_BASE}/sessions/{session_id}", headers=headers)
            except Exception:
                pass

            return {"status": "success", "ready": True, "photos_count": len(photos_to_save)}

    def save_uploaded_photo(self, account_id: int, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        img = Image.open(io.BytesIO(content_bytes)).convert("RGB")
        width, height = img.size
        unique_id = str(uuid.uuid4())[:12]
        local_filename = f"acc{account_id}_upload_{unique_id}.jpg"
        local_path = settings.THUMBNAILS_DIR / local_filename
        img.save(local_path, "JPEG", quality=settings.UPLOAD_JPEG_QUALITY)

        phash_val = str(imagehash.phash(img))
        dhash_val = str(imagehash.dhash(img))
        ahash_val = str(imagehash.average_hash(img))

        photo_data = [{
            "account_id": account_id,
            "google_id": f"upload_{unique_id}",
            "filename": filename,
            "mime_type": "image/jpeg",
            "base_url": "",
            "thumbnail_path": str(local_path),
            "creation_time": datetime.now(timezone.utc).isoformat(),
            "width": width,
            "height": height,
            "camera_make": "Uploaded",
            "camera_model": "Local",
            "phash": phash_val,
            "dhash": dhash_val,
            "ahash": ahash_val,
        }]
        self.photo_repo.save_photos(photo_data)
        return photo_data[0]

    async def fetch_photos_from_google(self, account_id: int, page_size: Optional[int] = None) -> List[Dict[str, Any]]:
        effective_page_size = page_size or settings.DEFAULT_PAGE_SIZE
        token = await auth_service.get_valid_token(account_id)
        if not token:
            raise ValueError(f"Account {account_id} is not authenticated")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        photos_to_save = []
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            url = f"{settings.GOOGLE_PHOTOS_MEDIA_URL}?pageSize={effective_page_size}"
            res = await client.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()

            media_items = data.get("mediaItems", [])
            for item in media_items:
                metadata = item.get("mediaMetadata", {})
                photo_info = metadata.get("photo", {})

                photos_to_save.append({
                    "account_id": account_id,
                    "google_id": item["id"],
                    "filename": item.get("filename"),
                    "mime_type": item.get("mimeType"),
                    "base_url": item.get("baseUrl"),
                    "creation_time": metadata.get("creationTime"),
                    "width": metadata.get("width", settings.DEFAULT_WIDTH),
                    "height": metadata.get("height", settings.DEFAULT_HEIGHT),
                    "camera_make": photo_info.get("cameraMake"),
                    "camera_model": photo_info.get("cameraModel"),
                })

        self.photo_repo.save_photos(photos_to_save)
        await self.process_thumbnails_and_hashes(photos_to_save, token=token)
        return photos_to_save

    async def process_thumbnails_and_hashes(
        self,
        photos: List[Dict[str, Any]],
        token: Optional[str] = None
    ) -> None:
        auth_headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            for p in photos:
                try:
                    base_url = p.get("base_url")
                    if not base_url:
                        continue
                    dim = settings.THUMBNAIL_MAX_DIMENSION
                    thumb_url = f"{base_url}=w{dim}-h{dim}"
                    res = await client.get(thumb_url)
                    if res.status_code in (401, 403) and auth_headers:
                        res = await client.get(thumb_url, headers=auth_headers)

                    if res.status_code == 200:
                        img = Image.open(io.BytesIO(res.content)).convert("RGB")
                        phash_val = str(imagehash.phash(img))
                        dhash_val = str(imagehash.dhash(img))
                        ahash_val = str(imagehash.average_hash(img))

                        filename = f"acc{p['account_id']}_{p['google_id'][:16]}.jpg"
                        local_path = settings.THUMBNAILS_DIR / filename
                        img.save(local_path, "JPEG", quality=settings.THUMBNAIL_JPEG_QUALITY)

                        row = self.photo_repo.get_by_account_and_google_id(p["account_id"], p["google_id"])
                        if row:
                            self.photo_repo.update_photo_hashes(
                                row["id"], str(local_path), phash_val, dhash_val, ahash_val
                            )
                except Exception as e:
                    print(f"Error processing photo {p.get('google_id')}: {e}")

    def get_photos(
        self,
        account_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        effective_limit = limit or settings.MAX_GALLERY_LIMIT
        return self.photo_repo.get_photos(account_id, start_date, end_date, effective_limit, offset)

    def get_date_bounds(self) -> Dict[str, Any]:
        return self.photo_repo.get_date_bounds()

photos_service = PhotosService()
