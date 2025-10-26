import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from ..config import settings
from datetime import datetime
from .exceptions import APIException

logger = logging.getLogger(__name__)


class OpenDotaAPI:
    """OpenDota API implementation for Dota 2"""

    def __init__(self, rate_limit_delay: float):
        self.rate_limit_delay = rate_limit_delay
        self.base_url = settings.OPENDOTA_API_BASE_URL

    async def _rate_limit_delay(self):
        """Apply rate limiting delay"""
        await asyncio.sleep(self.rate_limit_delay)

    async def get_match_history(
        self,
        account_id: int,
        matches_requested: int = 100,
        start_at_match_id: Optional[int] = None
    ) -> List[Dict]:
        """Get match history for a player"""
        url = f"{self.base_url}/players/{account_id}/matches"

        params = {"limit": matches_requested}

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """
        Get match details using OpenDota API

        Raises:
            APIException: When the API request fails, includes status_code
        """
        url = f"{self.base_url}/matches/{match_id}"

        logger.debug(f"Fetching match details for match_id={match_id}")

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                logger.debug(f"Match {match_id} response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Successfully fetched match details for match_id={match_id}")
                return data
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_text = e.response.text
                logger.error(f"HTTP error {status_code} fetching match {match_id}: {error_text}")
                raise APIException(
                    f"HTTP error fetching match {match_id}: {error_text}",
                    status_code=status_code
                )
            except httpx.RequestError as e:
                logger.error(f"Request error fetching match {match_id}: {str(e)}")
                raise APIException(f"Request error fetching match {match_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching match {match_id}: {str(e)}", exc_info=True)
                raise APIException(f"Unexpected error fetching match {match_id}: {str(e)}")

    async def get_heroes(self) -> List[Dict]:
        """Get heroes using OpenDota API"""
        url = f"{self.base_url}/heroes"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def normalize_match_data(self, match: Dict, account_id: int) -> Dict:
        """Normalize OpenDota API match data"""
        return {
            "match_id": match.get("match_id"),
            "start_time": datetime.fromtimestamp(match.get("start_time", 0)),
            "duration": match.get("duration"),
            "game_mode": match.get("game_mode"),
            "lobby_type": match.get("lobby_type"),
            "radiant_win": match.get("radiant_win"),
            "player_data": match,  # OpenDota returns player-specific data
            "all_players": match.get("players", []) if "players" in match else [],
            "raw_data": match,
        }
