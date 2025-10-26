import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from ..config import settings
from datetime import datetime
from .exceptions import APIException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OpenDotaAPI:
    """
    OpenDota API implementation for Dota 2

    Rate limits:
    - With API key: 1200 calls/min, unlimited per day, $0.0001 per call
    - Without API key: 60 calls/min, 2000 calls/day, free
    """

    COST_PER_CALL = 0.0001  # Cost when using API key

    def __init__(self, rate_limit_delay: float, api_key: Optional[str] = None):
        self.rate_limit_delay = rate_limit_delay
        self.base_url = settings.OPENDOTA_API_BASE_URL
        self.api_key = api_key
        logger.info(f"Initialized OpenDotaAPI with base_url={self.base_url}, rate_limit={rate_limit_delay}s, api_key={'set' if api_key else 'not set'}")

    async def _rate_limit_delay(self):
        """Apply rate limiting delay"""
        await asyncio.sleep(self.rate_limit_delay)

    def _track_api_call(self, db: Optional[Session], endpoint: str, status_code: int):
        """Track API call for cost monitoring"""
        if db is None:
            return

        try:
            from ..models import APICall

            cost = self.COST_PER_CALL if self.api_key else 0.0

            api_call = APICall(
                provider="opendota",
                endpoint=endpoint,
                used_api_key=bool(self.api_key),
                cost=cost,
                status_code=status_code
            )
            db.add(api_call)
            db.commit()

            if self.api_key:
                logger.debug(f"Tracked OpenDota API call: {endpoint} (cost: ${cost:.4f})")
        except Exception as e:
            logger.error(f"Failed to track API call: {e}")
            # Don't fail the request if tracking fails
            if db:
                db.rollback()

    async def get_match_history(
        self,
        account_id: int,
        matches_requested: int = 100,
        start_at_match_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """
        Get match history for a player

        Note: OpenDota uses offset-based pagination, not start_at_match_id.
        The start_at_match_id parameter is converted to offset internally.
        """
        endpoint = f"/players/{account_id}/matches"
        url = f"{self.base_url}{endpoint}"

        params = {"limit": min(matches_requested, 100)}

        if self.api_key:
            params["api_key"] = self.api_key

        # OpenDota uses offset, not start_at_match_id
        # If start_at_match_id is provided, use it as offset
        if start_at_match_id is not None:
            params["offset"] = start_at_match_id

        logger.info(f"Fetching match history for account_id={account_id}, limit={params['limit']}, offset={params.get('offset', 0)}")
        logger.debug(f"Request URL: {url}")

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                logger.debug(f"Response status: {response.status_code}")
                self._track_api_call(db, endpoint, response.status_code)
                response.raise_for_status()
                matches = response.json()
                logger.info(f"Successfully fetched {len(matches)} matches for account_id={account_id}")
                return matches
            except httpx.HTTPStatusError as e:
                self._track_api_call(db, endpoint, e.response.status_code)
                logger.error(f"HTTP error {e.response.status_code} fetching match history for account_id={account_id}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                self._track_api_call(db, endpoint, 0)
                logger.error(f"Request error fetching match history for account_id={account_id}: {str(e)}")
                raise
            except Exception as e:
                self._track_api_call(db, endpoint, 0)
                logger.error(f"Unexpected error fetching match history for account_id={account_id}: {str(e)}", exc_info=True)
                raise

    async def get_match_details(self, match_id: int, db: Optional[Session] = None) -> Optional[Dict]:
        """
        Get match details using OpenDota API

        Raises:
            APIException: When the API request fails, includes status_code
        """
        endpoint = f"/matches/{match_id}"
        url = f"{self.base_url}{endpoint}"

        params = {}
        if self.api_key:
            params["api_key"] = self.api_key

        logger.debug(f"Fetching match details for match_id={match_id}")

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                logger.debug(f"Match {match_id} response status: {response.status_code}")
                self._track_api_call(db, endpoint, response.status_code)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Successfully fetched match details for match_id={match_id}")
                return data
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_text = e.response.text
                self._track_api_call(db, endpoint, status_code)
                logger.error(f"HTTP error {status_code} fetching match {match_id}: {error_text}")
                raise APIException(
                    f"HTTP error fetching match {match_id}: {error_text}",
                    status_code=status_code
                )
            except httpx.RequestError as e:
                self._track_api_call(db, endpoint, 0)
                logger.error(f"Request error fetching match {match_id}: {str(e)}")
                raise APIException(f"Request error fetching match {match_id}: {str(e)}")
            except Exception as e:
                self._track_api_call(db, endpoint, 0)
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
        """
        Normalize OpenDota API match data

        Note: OpenDota's /matches/{match_id} endpoint returns full match data with all players,
        while /players/{account_id}/matches returns player-centric summaries.
        This function handles the full match details format.
        """
        # Find player in match
        player_data = None
        for player in match.get("players", []):
            if player.get("account_id") == account_id:
                player_data = player
                break

        if not player_data:
            logger.error(f"Could not find player {account_id} in match {match.get('match_id')}")
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
