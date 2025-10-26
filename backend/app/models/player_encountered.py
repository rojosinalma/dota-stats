from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class PlayerEncountered(Base):
    __tablename__ = "players_encountered"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    persona_name = Column(String)

    # Statistics
    games_together = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    games_lost = Column(Integer, default=0)

    first_match_at = Column(DateTime(timezone=True))
    last_match_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'account_id', name='uq_user_player'),
    )
