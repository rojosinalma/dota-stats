from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)  # Steam ID 64
    steam_id = Column(String, unique=True, index=True, nullable=False)
    persona_name = Column(String, nullable=False)
    profile_url = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
