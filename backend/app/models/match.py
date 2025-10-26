from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(BigInteger, primary_key=True, index=True)  # Match ID
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # Two-phase sync columns
    has_details = Column(Boolean, nullable=True, index=True)  # NULL=stub, TRUE=complete, FALSE=failed
    retry_count = Column(Integer, nullable=False, default=0)
    last_fetch_attempt = Column(DateTime(timezone=True), nullable=True)
    fetch_error = Column(String, nullable=True)

    # Match data (nullable to support stubs without details)
    start_time = Column(DateTime(timezone=True), nullable=True, index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    game_mode = Column(Integer, nullable=True, index=True)
    lobby_type = Column(Integer, nullable=True, index=True)
    radiant_win = Column(Boolean, nullable=True)

    # User-specific match data
    hero_id = Column(Integer, nullable=True, index=True)
    player_slot = Column(Integer, nullable=True)
    radiant_team = Column(Boolean, nullable=True)

    # Player stats
    kills = Column(Integer, nullable=True)
    deaths = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    last_hits = Column(Integer)
    denies = Column(Integer)
    gold_per_min = Column(Integer)
    xp_per_min = Column(Integer)
    hero_damage = Column(Integer)
    tower_damage = Column(Integer)
    hero_healing = Column(Integer)
    level = Column(Integer)

    # Items (item IDs)
    item_0 = Column(Integer)
    item_1 = Column(Integer)
    item_2 = Column(Integer)
    item_3 = Column(Integer)
    item_4 = Column(Integer)
    item_5 = Column(Integer)
    backpack_0 = Column(Integer)
    backpack_1 = Column(Integer)
    backpack_2 = Column(Integer)
    item_neutral = Column(Integer)

    # Abilities (stored as JSON array)
    ability_upgrades = Column(JSON)

    # Additional stats
    net_worth = Column(Integer)
    rank_tier = Column(Integer)  # MMR tier

    # Full match data (cached from API)
    raw_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(BigInteger, ForeignKey("matches.id"), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=True, index=True)  # Can be null for anonymous
    player_slot = Column(Integer, nullable=False)
    hero_id = Column(Integer, nullable=False)

    # Player stats
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    gold_per_min = Column(Integer)
    xp_per_min = Column(Integer)
    hero_damage = Column(Integer)
    tower_damage = Column(Integer)
    hero_healing = Column(Integer)
    last_hits = Column(Integer)
    denies = Column(Integer)
    level = Column(Integer)
    net_worth = Column(Integer)

    # Items
    item_0 = Column(Integer)
    item_1 = Column(Integer)
    item_2 = Column(Integer)
    item_3 = Column(Integer)
    item_4 = Column(Integer)
    item_5 = Column(Integer)

    # Relationship
    match = relationship("Match", back_populates="players")
