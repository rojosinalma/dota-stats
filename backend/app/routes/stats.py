from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..database import get_db
from ..models import User
from ..schemas.stats import HeroStats, PlayerStats, TimeStats, DashboardStats, PlayerEncounteredStats
from ..services import StatsService
from .auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dashboard statistics"""
    stats_service = StatsService(db)
    return stats_service.get_dashboard_stats(user.id)


@router.get("/player", response_model=PlayerStats)
async def get_player_stats(
    hero_id: Optional[int] = None,
    game_mode: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get player statistics with filters"""
    stats_service = StatsService(db)
    return stats_service.get_player_stats(
        user.id,
        hero_id=hero_id,
        game_mode=game_mode,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/heroes", response_model=List[HeroStats])
async def get_hero_stats(
    hero_id: Optional[int] = None,
    game_mode: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = Query(None, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get per-hero statistics"""
    stats_service = StatsService(db)
    return stats_service.get_hero_stats(
        user.id,
        hero_id=hero_id,
        game_mode=game_mode,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/players-encountered", response_model=List[PlayerEncounteredStats])
async def get_players_encountered(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get frequently played with players"""
    stats_service = StatsService(db)
    return stats_service.get_players_encountered(user.id, limit=limit)


@router.get("/time-based", response_model=List[TimeStats])
async def get_time_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get time-based statistics"""
    stats_service = StatsService(db)
    return stats_service.get_time_based_stats(user.id)
