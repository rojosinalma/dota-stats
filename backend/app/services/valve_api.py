import httpx
import asyncio
from typing import List, Dict, Optional
from ..config import settings
from datetime import datetime


class ValveAPI:
    """Valve Web API implementation for Dota 2"""

    def __init__(self, api_key: str, rate_limit_delay: float):
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.base_url = settings.VALVE_API_BASE_URL

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

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("matches", [])

    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get match details using Valve Web API"""
        url = f"{self.base_url}/IDOTA2Match_570/GetMatchDetails/v1/"

        params = {
            "key": self.api_key,
            "match_id": match_id,
        }

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("result")
            except httpx.HTTPError:
                return None

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
