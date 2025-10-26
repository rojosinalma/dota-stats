import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from ..config import settings
from datetime import datetime
from .exceptions import APIException

logger = logging.getLogger(__name__)


class ValveAPI:
    """Valve Web API implementation for Dota 2"""

    def __init__(self, api_key: str, rate_limit_delay: float):
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.base_url = settings.VALVE_API_BASE_URL
        logger.info(f"Initialized ValveAPI with base_url={self.base_url}, rate_limit={rate_limit_delay}s")

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
        url = f"{self.base_url}/IDOTA2Match_570/GetMatchHistory/v1/"

        params = {
            "key": self.api_key,
            "account_id": account_id,
            "matches_requested": min(matches_requested, 100),  # API limit
        }

        if start_at_match_id:
            params["start_at_match_id"] = start_at_match_id

        logger.info(f"Fetching match history for account_id={account_id}, matches_requested={matches_requested}, start_at={start_at_match_id}")
        logger.debug(f"Request URL: {url}")

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                matches = data.get("result", {}).get("matches", [])
                logger.info(f"Successfully fetched {len(matches)} matches for account_id={account_id}")
                return matches
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} fetching match history for account_id={account_id}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error fetching match history for account_id={account_id}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching match history for account_id={account_id}: {str(e)}", exc_info=True)
                raise

    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """
        Get match details using Valve Web API

        Raises:
            APIException: When the API request fails, includes status_code
        """
        url = f"{self.base_url}/IDOTA2Match_570/GetMatchDetails/v1/"

        params = {
            "key": self.api_key,
            "match_id": match_id,
        }

        logger.debug(f"Fetching match details for match_id={match_id}")

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                logger.debug(f"Match {match_id} response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Successfully fetched match details for match_id={match_id}")
                return data.get("result")
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
        """Get heroes using Valve Web API"""
        url = f"{self.base_url}/IEconDOTA2_570/GetHeroes/v1/"

        params = {
            "key": self.api_key,
            "language": "en_us",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("heroes", [])

    def normalize_match_data(self, match: Dict, account_id: int) -> Dict:
        """Normalize Valve API match data"""
        # Find player in match
        player_data = None
        for player in match.get("players", []):
            if player.get("account_id") == account_id:
                player_data = player
                break

        if not player_data:
            return None

        return {
            "match_id": match.get("match_id"),
            "start_time": datetime.fromtimestamp(match.get("start_time", 0)),
            "duration": match.get("duration"),
            "game_mode": match.get("game_mode"),
            "lobby_type": match.get("lobby_type"),
            "radiant_win": match.get("radiant_win"),
            "player_data": player_data,
            "all_players": match.get("players", []),
            "raw_data": match,
        }
