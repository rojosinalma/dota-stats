import httpx
import asyncio
from typing import List, Dict, Optional
from ..config import settings
from datetime import datetime


class DotaAPIService:
    def __init__(self):
        self.provider = settings.API_PROVIDER
        self.api_key = settings.STEAM_API_KEY
        self.rate_limit_delay = settings.RATE_LIMIT_DELAY

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
        if self.provider == "valve":
            return await self._get_match_history_valve(account_id, matches_requested, start_at_match_id)
        else:
            return await self._get_match_history_opendota(account_id, matches_requested)

    async def _get_match_history_valve(
        self,
        account_id: int,
        matches_requested: int = 100,
        start_at_match_id: Optional[int] = None
    ) -> List[Dict]:
        """Get match history using Valve Web API"""
        url = f"{settings.VALVE_API_BASE_URL}/IDOTA2Match_570/GetMatchHistory/v1/"

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

    async def _get_match_history_opendota(
        self,
        account_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """Get match history using OpenDota API"""
        url = f"{settings.OPENDOTA_API_BASE_URL}/players/{account_id}/matches"

        params = {"limit": limit}

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed match information"""
        if self.provider == "valve":
            return await self._get_match_details_valve(match_id)
        else:
            return await self._get_match_details_opendota(match_id)

    async def _get_match_details_valve(self, match_id: int) -> Optional[Dict]:
        """Get match details using Valve Web API"""
        url = f"{settings.VALVE_API_BASE_URL}/IDOTA2Match_570/GetMatchDetails/v1/"

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

    async def _get_match_details_opendota(self, match_id: int) -> Optional[Dict]:
        """Get match details using OpenDota API"""
        url = f"{settings.OPENDOTA_API_BASE_URL}/matches/{match_id}"

        await self._rate_limit_delay()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None

    async def get_heroes(self) -> List[Dict]:
        """Get list of all heroes"""
        if self.provider == "valve":
            return await self._get_heroes_valve()
        else:
            return await self._get_heroes_opendota()

    async def _get_heroes_valve(self) -> List[Dict]:
        """Get heroes using Valve Web API"""
        url = f"{settings.VALVE_API_BASE_URL}/IEconDOTA2_570/GetHeroes/v1/"

        params = {
            "key": self.api_key,
            "language": "en_us",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", {}).get("heroes", [])

    async def _get_heroes_opendota(self) -> List[Dict]:
        """Get heroes using OpenDota API"""
        url = f"{settings.OPENDOTA_API_BASE_URL}/heroes"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def normalize_match_data(self, match_data: Dict, account_id: int) -> Dict:
        """Normalize match data from different API providers"""
        if self.provider == "valve":
            return self._normalize_valve_match(match_data, account_id)
        else:
            return self._normalize_opendota_match(match_data, account_id)

    def _normalize_valve_match(self, match: Dict, account_id: int) -> Dict:
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

    def _normalize_opendota_match(self, match: Dict, account_id: int) -> Dict:
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
