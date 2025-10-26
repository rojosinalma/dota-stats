from pydantic import BaseModel
from typing import List, Dict, Optional


class HeroStats(BaseModel):
    hero_id: int
    hero_name: Optional[str] = None
    games_played: int
    wins: int
    losses: int
    win_rate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_kda: float
    avg_gpm: Optional[float] = None
    avg_xpm: Optional[float] = None
    total_hero_damage: Optional[int] = None
    total_tower_damage: Optional[int] = None
    total_hero_healing: Optional[int] = None


class PlayerEncounteredStats(BaseModel):
    account_id: int
    persona_name: Optional[str] = None
    games_together: int
    games_won: int
    games_lost: int
    win_rate: float


class TimeStats(BaseModel):
    period: str  # daily, weekly, monthly, etc.
    start_date: str
    end_date: str
    total_games: int
    wins: int
    losses: int
    win_rate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_kda: float
    avg_gpm: Optional[float] = None
    avg_xpm: Optional[float] = None


class PlayerStats(BaseModel):
    total_matches: int
    total_wins: int
    total_losses: int
    win_rate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_kda: float
    avg_gpm: Optional[float] = None
    avg_xpm: Optional[float] = None
    most_played_heroes: List[HeroStats]
    recent_matches: int
    last_match_time: Optional[str] = None


class DashboardStats(BaseModel):
    player_stats: PlayerStats
    hero_stats: List[HeroStats]
    players_encountered: List[PlayerEncounteredStats]
    time_stats: List[TimeStats]
