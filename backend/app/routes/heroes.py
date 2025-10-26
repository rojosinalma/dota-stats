from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Hero

router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("")
async def get_heroes(db: Session = Depends(get_db)):
    """Get list of all Dota 2 heroes"""
    heroes = db.query(Hero).all()
    return heroes
