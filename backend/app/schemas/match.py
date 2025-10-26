from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class MatchPlayerResponse(BaseModel):
    account_id: Optional[int] = None
    hero_id: int
    player_slot: int
    kills: Optional[int] = None
    deaths: Optional[int] = None
    assists: Optional[int] = None
    gold_per_min: Optional[int] = None
    xp_per_min: Optional[int] = None
    hero_damage: Optional[int] = None
    tower_damage: Optional[int] = None
    hero_healing: Optional[int] = None
    last_hits: Optional[int] = None
    denies: Optional[int] = None
    level: Optional[int] = None
    net_worth: Optional[int] = None

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    start_time: datetime
    duration: int
    game_mode: int
    lobby_type: int
    radiant_win: bool
    hero_id: int
    player_slot: int
    radiant_team: bool
    kills: int
    deaths: int
    assists: int
    gold_per_min: Optional[int] = None
    xp_per_min: Optional[int] = None
    hero_damage: Optional[int] = None

    @property
    def won(self) -> bool:
        return self.radiant_team == self.radiant_win

    @property
    def kda_ratio(self) -> float:
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return (self.kills + self.assists) / self.deaths

    class Config:
        from_attributes = True


class MatchDetailResponse(MatchResponse):
    tower_damage: Optional[int] = None
    hero_healing: Optional[int] = None
    last_hits: Optional[int] = None
    denies: Optional[int] = None
    level: Optional[int] = None
    net_worth: Optional[int] = None
    item_0: Optional[int] = None
    item_1: Optional[int] = None
    item_2: Optional[int] = None
    item_3: Optional[int] = None
    item_4: Optional[int] = None
    item_5: Optional[int] = None
    backpack_0: Optional[int] = None
    backpack_1: Optional[int] = None
    backpack_2: Optional[int] = None
    item_neutral: Optional[int] = None
    ability_upgrades: Optional[List[Any]] = None
    rank_tier: Optional[int] = None
    players: List[MatchPlayerResponse] = []

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int
    page: int
    page_size: int
