from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from ..database import Base


class APICall(Base):
    """Track API calls made to external services (OpenDota, Valve)"""

    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False, index=True)  # 'opendota' or 'valve'
    endpoint = Column(String, nullable=False)  # e.g., '/matches/{id}', '/players/{id}/matches'
    used_api_key = Column(Boolean, default=False)  # Whether API key was used
    cost = Column(Float, default=0.0)  # Cost of the call (0.0001 for OpenDota with key)
    status_code = Column(Integer)  # HTTP status code
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<APICall(provider={self.provider}, endpoint={self.endpoint}, cost={self.cost})>"
