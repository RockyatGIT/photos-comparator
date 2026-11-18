from typing import Optional, List, Dict, Any
from ..core.database import get_db_connection
from .photo_repo import PhotoRepository

class MatchRepository:
    @staticmethod
    def save_matches(matches: List[Dict[str, Any]]) -> None:
        if not matches:
            return
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM matches") # clear previous run
            for m in matches:
                cursor.execute("""
                INSERT INTO matches (photo_id_1, photo_id_2, phash_distance, similarity_score, match_type, time_diff_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(photo_id_1, photo_id_2) DO UPDATE SET
                    phash_distance=excluded.phash_distance,
                    similarity_score=excluded.similarity_score,
                    match_type=excluded.match_type,
                    time_diff_seconds=excluded.time_diff_seconds
                """, (
                    m["photo_id_1"], m["photo_id_2"], m["phash_distance"],
                    m["similarity_score"], m["match_type"], m.get("time_diff_seconds")
                ))

    @staticmethod
    def get_matches(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        s_date, e_date = PhotoRepository.normalize_date_range(start_date, end_date)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT 
                m.id as match_id,
                m.phash_distance,
                m.similarity_score,
                m.match_type,
                m.time_diff_seconds,
                p1.id as p1_id, p1.google_id as p1_google_id, p1.filename as p1_filename, p1.creation_time as p1_creation_time,
                p1.width as p1_width, p1.height as p1_height, p1.thumbnail_path as p1_thumbnail, p1.base_url as p1_base_url,
                p2.id as p2_id, p2.google_id as p2_google_id, p2.filename as p2_filename, p2.creation_time as p2_creation_time,
                p2.width as p2_width, p2.height as p2_height, p2.thumbnail_path as p2_thumbnail, p2.base_url as p2_base_url
            FROM matches m
            JOIN photos p1 ON m.photo_id_1 = p1.id
            JOIN photos p2 ON m.photo_id_2 = p2.id
            WHERE m.dismissed = 0
            """
            params: List[Any] = []
            if s_date:
                query += " AND (p1.creation_time >= ? OR p2.creation_time >= ?)"
                params.extend([s_date, s_date])
            if e_date:
                query += " AND (p1.creation_time <= ? OR p2.creation_time <= ?)"
                params.extend([e_date, e_date])

            query += " ORDER BY m.similarity_score DESC, m.phash_distance ASC"
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def count() -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM matches WHERE dismissed = 0")
            row = cursor.fetchone()
            return row[0] if row else 0
