from typing import Optional, List, Dict, Any, Tuple
from ..core.database import get_db_connection

class PhotoRepository:
    @staticmethod
    def normalize_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        s = start_date.strip() if start_date else None
        e = end_date.strip() if end_date else None
        if e and len(e) == 10:
            e = f"{e}T23:59:59.999Z"
        return s, e

    @staticmethod
    def save_photos(photos: List[Dict[str, Any]]) -> None:
        if not photos:
            return
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for p in photos:
                cursor.execute("""
                INSERT INTO photos (
                    account_id, google_id, filename, mime_type, base_url, thumbnail_path,
                    creation_time, width, height, camera_make, camera_model, phash, dhash, ahash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, google_id) DO UPDATE SET
                    filename=excluded.filename,
                    mime_type=excluded.mime_type,
                    base_url=excluded.base_url,
                    thumbnail_path=COALESCE(excluded.thumbnail_path, photos.thumbnail_path),
                    creation_time=excluded.creation_time,
                    width=excluded.width,
                    height=excluded.height,
                    camera_make=excluded.camera_make,
                    camera_model=excluded.camera_model,
                    phash=COALESCE(excluded.phash, photos.phash),
                    dhash=COALESCE(excluded.dhash, photos.dhash),
                    ahash=COALESCE(excluded.ahash, photos.ahash)
                """, (
                    p["account_id"], p["google_id"], p.get("filename"), p.get("mime_type"),
                    p.get("base_url"), p.get("thumbnail_path"), p.get("creation_time"),
                    p.get("width"), p.get("height"), p.get("camera_make"), p.get("camera_model"),
                    p.get("phash"), p.get("dhash"), p.get("ahash")
                ))

    @staticmethod
    def update_photo_hashes(photo_id: int, thumbnail_path: str, phash: str, dhash: str, ahash: str) -> None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE photos SET thumbnail_path = ?, phash = ?, dhash = ?, ahash = ?
            WHERE id = ?
            """, (thumbnail_path, phash, dhash, ahash, photo_id))

    @staticmethod
    def get_photos(
        account_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        s_date, e_date = PhotoRepository.normalize_date_range(start_date, end_date)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM photos WHERE account_id = ?"
            params: List[Any] = [account_id]

            if s_date:
                query += " AND creation_time >= ?"
                params.append(s_date)
            if e_date:
                query += " AND creation_time <= ?"
                params.append(e_date)

            query += " ORDER BY creation_time DESC, id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_photos_for_matching(
        account_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        s_date, e_date = PhotoRepository.normalize_date_range(start_date, end_date)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT id, account_id, google_id, filename, creation_time, width, height, phash, dhash, ahash, thumbnail_path, base_url
            FROM photos
            WHERE account_id = ? AND phash IS NOT NULL
            """
            params: List[Any] = [account_id]
            if s_date:
                query += " AND creation_time >= ?"
                params.append(s_date)
            if e_date:
                query += " AND creation_time <= ?"
                params.append(e_date)

            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_unique_photos(
        account_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        s_date, e_date = PhotoRepository.normalize_date_range(start_date, end_date)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            photo_col = "photo_id_1" if account_id == 1 else "photo_id_2"
            query = f"""
            SELECT * FROM photos
            WHERE account_id = ? AND id NOT IN (SELECT {photo_col} FROM matches WHERE dismissed = 0)
            """
            params: List[Any] = [account_id]
            if s_date:
                query += " AND creation_time >= ?"
                params.append(s_date)
            if e_date:
                query += " AND creation_time <= ?"
                params.append(e_date)

            query += " ORDER BY creation_time DESC"
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_date_bounds() -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                MIN(SUBSTR(creation_time, 1, 10)) as min_date,
                MAX(SUBSTR(creation_time, 1, 10)) as max_date,
                COUNT(*) as total_photos
            FROM photos
            WHERE creation_time IS NOT NULL AND creation_time != ''
            """)
            row = cursor.fetchone()
            return {
                "min_date": row["min_date"] if row and row["min_date"] else None,
                "max_date": row["max_date"] if row and row["max_date"] else None,
                "total_photos": row["total_photos"] if row else 0
            }

    @staticmethod
    def count(account_id: int) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM photos WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()
            return row["cnt"] if row else 0

    @staticmethod
    def get_by_account_and_google_id(account_id: int, google_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM photos WHERE account_id = ? AND google_id = ?", (account_id, google_id))
            row = cursor.fetchone()
            return dict(row) if row else None
