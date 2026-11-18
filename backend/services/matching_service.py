from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import imagehash

from ..core.config import settings
from ..repositories.photo_repo import PhotoRepository
from ..repositories.match_repo import MatchRepository

class MatchingService:
    def __init__(
        self,
        photo_repo: PhotoRepository = PhotoRepository,
        match_repo: MatchRepository = MatchRepository
    ):
        self.photo_repo = photo_repo
        self.match_repo = match_repo

    @staticmethod
    def parse_iso(ts: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None

    def compute_matches(
        self,
        max_distance: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        effective_max_distance = max_distance if max_distance is not None else settings.DEFAULT_MATCH_DISTANCE

        photos_acc1 = self.photo_repo.get_photos_for_matching(account_id=1, start_date=start_date, end_date=end_date)
        photos_acc2 = self.photo_repo.get_photos_for_matching(account_id=2, start_date=start_date, end_date=end_date)

        if not photos_acc1 or not photos_acc2:
            return {
                "status": "insufficient_data",
                "message": "Both accounts must have photos in the selected date range to run duplicate comparison",
                "start_date": start_date,
                "end_date": end_date,
                "scanned_acc1": len(photos_acc1),
                "scanned_acc2": len(photos_acc2),
                "total_matches": 0,
                "matches": []
            }

        # Pre-parse hashes
        parsed_acc1 = []
        for p in photos_acc1:
            try:
                h = imagehash.hex_to_hash(p["phash"])
                t = self.parse_iso(p["creation_time"]) if p.get("creation_time") else None
                parsed_acc1.append((p, h, t))
            except Exception:
                continue

        parsed_acc2 = []
        for p in photos_acc2:
            try:
                h = imagehash.hex_to_hash(p["phash"])
                t = self.parse_iso(p["creation_time"]) if p.get("creation_time") else None
                parsed_acc2.append((p, h, t))
            except Exception:
                continue

        candidate_pairs = []
        for p1, h1, t1 in parsed_acc1:
            for p2, h2, t2 in parsed_acc2:
                dist = int(h1 - h2)
                if dist <= effective_max_distance:
                    time_diff = abs((t1 - t2).total_seconds()) if (t1 and t2) else float("inf")
                    candidate_pairs.append((dist, time_diff, p1, p2))

        # Sort candidates: smallest hash distance first, then smallest time difference
        candidate_pairs.sort(key=lambda x: (x[0], x[1]))

        used_p1 = set()
        used_p2 = set()
        matched_pairs = []

        for dist, time_diff, p1, p2 in candidate_pairs:
            if p1["id"] in used_p1 or p2["id"] in used_p2:
                continue
            used_p1.add(p1["id"])
            used_p2.add(p2["id"])

            similarity = round(max(0.0, (1.0 - (float(dist) / settings.MAX_HASH_BITS)) * 100.0), 1)

            if dist <= settings.EXACT_MATCH_DISTANCE:
                match_type = "exact"
            elif dist <= settings.NEAR_DUPLICATE_DISTANCE:
                match_type = "duplicate"
            else:
                match_type = "similar"

            matched_pairs.append({
                "photo_id_1": p1["id"],
                "photo_id_2": p2["id"],
                "phash_distance": dist,
                "similarity_score": similarity,
                "match_type": match_type,
                "time_diff_seconds": time_diff if time_diff != float("inf") else None,
            })

        # Save to repository
        self.match_repo.save_matches(matched_pairs)

        all_matches = self.match_repo.get_matches(start_date=start_date, end_date=end_date)
        unique_acc1 = self.photo_repo.get_unique_photos(1, start_date=start_date, end_date=end_date)
        unique_acc2 = self.photo_repo.get_unique_photos(2, start_date=start_date, end_date=end_date)

        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "scanned_acc1": len(photos_acc1),
            "scanned_acc2": len(photos_acc2),
            "total_matches": len(all_matches),
            "exact_matches": sum(1 for m in all_matches if m["match_type"] == "exact"),
            "duplicate_matches": sum(1 for m in all_matches if m["match_type"] == "duplicate"),
            "similar_matches": sum(1 for m in all_matches if m["match_type"] == "similar"),
            "unique_in_account_1": len(unique_acc1),
            "unique_in_account_2": len(unique_acc2),
            "matches": all_matches
        }

    def get_matches(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.match_repo.get_matches(start_date=start_date, end_date=end_date)

    def get_unique_photos(
        self,
        account_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.photo_repo.get_unique_photos(account_id, start_date=start_date, end_date=end_date)

matching_service = MatchingService()
