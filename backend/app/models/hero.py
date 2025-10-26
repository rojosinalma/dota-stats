from sqlalchemy import Column, Integer, String, JSON
from ..database import Base


class Hero(Base):
    __tablename__ = "heroes"

    id = Column(Integer, primary_key=True, index=True)  # Hero ID from Dota 2
    name = Column(String, nullable=False, unique=True)
    localized_name = Column(String, nullable=False)
    primary_attr = Column(String)
    attack_type = Column(String)
    roles = Column(JSON)  # Array of roles
    img = Column(String)  # Image URL
    icon = Column(String)  # Icon URL
