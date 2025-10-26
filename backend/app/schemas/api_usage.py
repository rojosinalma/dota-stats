from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class APIUsageStats(BaseModel):
    """Statistics for API usage"""
    provider: str  # 'opendota' or 'valve'
    total_calls: int
    calls_with_key: int
    calls_without_key: int
    total_cost: float  # Total cost in USD
    success_calls: int  # HTTP 200-299
    failed_calls: int  # HTTP 400-599
    error_calls: int  # Network errors (status_code = 0)


class APIUsageSummary(BaseModel):
    """Overall API usage summary"""
    opendota_stats: Optional[APIUsageStats] = None
    valve_stats: Optional[APIUsageStats] = None
    total_cost: float
    total_calls: int
    has_api_key: bool
    daily_limit_remaining: Optional[int] = None  # For OpenDota without key
    estimated_monthly_cost: float  # Extrapolated from current usage


class DailyAPIUsage(BaseModel):
    """API usage for a specific day"""
    date: datetime
    provider: str
    total_calls: int
    total_cost: float
    success_calls: int
    failed_calls: int
