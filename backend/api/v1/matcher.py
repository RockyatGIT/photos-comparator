from typing import Optional
from fastapi import APIRouter, Query, Depends
from ...core.config import settings
from ...services.matching_service import MatchingService
from ...schemas.match import MatchListResponse, RunMatchResponse, UnmatchedListResponse
from ..deps import get_matching_service

router = APIRouter(prefix="/matcher", tags=["Matcher"])

@router.post("/run", response_model=RunMatchResponse)
def run_matcher(
    max_distance: int = Query(settings.DEFAULT_MATCH_DISTANCE, ge=0, le=30),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    matcher_srv: MatchingService = Depends(get_matching_service)
):
    """Executes perceptual hashing comparison for photos across both accounts with optional date filtering."""
    result = matcher_srv.compute_matches(max_distance=max_distance, start_date=start_date, end_date=end_date)
    return result

@router.get("/matches", response_model=MatchListResponse)
def list_matches(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    matcher_srv: MatchingService = Depends(get_matching_service)
):
    """Lists duplicate and similar photo pairs found between Account 1 and Account 2."""
    matches = matcher_srv.get_matches(start_date=start_date, end_date=end_date)
    return {"total": len(matches), "matches": matches, "start_date": start_date, "end_date": end_date}

@router.get("/unmatched", response_model=UnmatchedListResponse)
def list_unmatched(
    account: int = Query(..., ge=1, le=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    matcher_srv: MatchingService = Depends(get_matching_service)
):
    """Lists photos unique to the specified account that have no match in the counterpart account."""
    photos = matcher_srv.get_unique_photos(account, start_date=start_date, end_date=end_date)
    return {"account_id": account, "total": len(photos), "photos": photos, "start_date": start_date, "end_date": end_date}
