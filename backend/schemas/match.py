from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class MatchListResponse(BaseModel):
    total: int
    matches: List[Dict[str, Any]]
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class RunMatchResponse(BaseModel):
    status: str
    message: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    scanned_acc1: Optional[int] = None
    scanned_acc2: Optional[int] = None
    total_matches: int = 0
    exact_matches: int = 0
    duplicate_matches: int = 0
    similar_matches: int = 0
    unique_in_account_1: int = 0
    unique_in_account_2: int = 0
    matches: List[Dict[str, Any]] = []

class UnmatchedListResponse(BaseModel):
    account_id: int
    total: int
    photos: List[Dict[str, Any]]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
