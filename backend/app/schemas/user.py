from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: int
    steam_id: str
    persona_name: str
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True
