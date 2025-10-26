from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Match
from ..schemas import MatchListResponse, MatchResponse, MatchDetailResponse
from .auth import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
async def get_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    hero_id: Optional[int] = None,
    game_mode: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of matches with filters"""
    query = db.query(Match).filter(Match.user_id == user.id)

    # Apply filters
    if hero_id:
        query = query.filter(Match.hero_id == hero_id)
    if game_mode:
        query = query.filter(Match.game_mode == game_mode)
    if start_date:
        query = query.filter(Match.start_time >= start_date)
    if end_date:
        query = query.filter(Match.start_time <= end_date)

    # Get total count
    total = query.count()

    # Apply pagination
    query = query.order_by(Match.start_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    matches = query.all()

    return MatchListResponse(
        matches=matches,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{match_id}", response_model=MatchDetailResponse)
async def get_match(
    match_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed match information"""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == user.id)
        .first()
    )

    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Match not found")

    return match
