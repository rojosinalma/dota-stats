from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
import logging
from ..database import get_db
from ..models import User, APICall
from ..schemas import APIUsageStats, APIUsageSummary, DailyAPIUsage
from .auth import get_current_user
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-usage", tags=["api-usage"])


@router.get("/summary", response_model=APIUsageSummary)
async def get_api_usage_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get overall API usage summary"""

    try:
        # Get OpenDota stats
        opendota_calls = db.query(APICall).filter(APICall.provider == "opendota").all()
        opendota_stats = _calculate_stats("opendota", opendota_calls) if opendota_calls else None

        # Get Valve stats
        valve_calls = db.query(APICall).filter(APICall.provider == "valve").all()
        valve_stats = _calculate_stats("valve", valve_calls) if valve_calls else None
    except Exception as e:
        logger.error(f"Error fetching API calls: {e}")
        opendota_stats = None
        valve_stats = None

    total_cost = (opendota_stats.total_cost if opendota_stats else 0) + \
                 (valve_stats.total_cost if valve_stats else 0)

    total_calls = (opendota_stats.total_calls if opendota_stats else 0) + \
                  (valve_stats.total_calls if valve_stats else 0)

    # Calculate daily limit remaining for OpenDota without key
    daily_limit_remaining = None
    if not settings.OPENDOTA_API_KEY and opendota_stats:
        # Get calls made today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        calls_today = db.query(func.count(APICall.id)).filter(
            APICall.provider == "opendota",
            APICall.created_at >= today_start
        ).scalar()
        daily_limit_remaining = max(0, 2000 - (calls_today or 0))

    # Estimate monthly cost (assuming current rate continues)
    estimated_monthly_cost = 0.0
    if opendota_stats and opendota_stats.calls_with_key > 0:
        # Calculate average calls per day
        first_call = db.query(APICall).filter(
            APICall.provider == "opendota",
            APICall.used_api_key == True
        ).order_by(APICall.created_at).first()

        if first_call:
            days_since_first = (datetime.utcnow() - first_call.created_at).days + 1
            avg_calls_per_day = opendota_stats.calls_with_key / max(days_since_first, 1)
            estimated_monthly_cost = avg_calls_per_day * 30 * 0.0001

    return APIUsageSummary(
        opendota_stats=opendota_stats,
        valve_stats=valve_stats,
        total_cost=total_cost,
        total_calls=total_calls,
        has_api_key=bool(settings.OPENDOTA_API_KEY),
        daily_limit_remaining=daily_limit_remaining,
        estimated_monthly_cost=estimated_monthly_cost
    )


@router.get("/daily", response_model=List[DailyAPIUsage])
async def get_daily_api_usage(
    days: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get daily API usage for the last N days"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Query daily stats
    daily_stats = db.query(
        func.date_trunc('day', APICall.created_at).label('date'),
        APICall.provider,
        func.count(APICall.id).label('total_calls'),
        func.sum(APICall.cost).label('total_cost'),
        func.sum(func.cast((APICall.status_code >= 200) & (APICall.status_code < 300), func.Integer)).label('success_calls'),
        func.sum(func.cast((APICall.status_code >= 400), func.Integer)).label('failed_calls')
    ).filter(
        APICall.created_at >= start_date
    ).group_by(
        func.date_trunc('day', APICall.created_at),
        APICall.provider
    ).order_by(
        func.date_trunc('day', APICall.created_at).desc()
    ).all()

    return [
        DailyAPIUsage(
            date=stat.date,
            provider=stat.provider,
            total_calls=stat.total_calls or 0,
            total_cost=float(stat.total_cost or 0),
            success_calls=stat.success_calls or 0,
            failed_calls=stat.failed_calls or 0
        )
        for stat in daily_stats
    ]


def _calculate_stats(provider: str, calls: List[APICall]) -> APIUsageStats:
    """Calculate statistics from API calls"""
    total_calls = len(calls)
    calls_with_key = sum(1 for c in calls if c.used_api_key)
    calls_without_key = total_calls - calls_with_key
    total_cost = sum(c.cost for c in calls)
    success_calls = sum(1 for c in calls if c.status_code and 200 <= c.status_code < 300)
    failed_calls = sum(1 for c in calls if c.status_code and c.status_code >= 400)
    error_calls = sum(1 for c in calls if not c.status_code or c.status_code == 0)

    return APIUsageStats(
        provider=provider,
        total_calls=total_calls,
        calls_with_key=calls_with_key,
        calls_without_key=calls_without_key,
        total_cost=total_cost,
        success_calls=success_calls,
        failed_calls=failed_calls,
        error_calls=error_calls
    )
