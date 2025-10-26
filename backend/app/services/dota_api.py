from typing import List, Dict, Optional
from ..config import settings
from .valve_api import ValveAPI
from .opendota_api import OpenDotaAPI


class DotaAPIService:
    """
    Factory/Router service that delegates API calls to the appropriate provider
    based on settings configuration.
    """

    def __init__(self):
        self.provider = settings.API_PROVIDER

        # Initialize the appropriate API implementation
        if self.provider == "valve":
            self.api = ValveAPI(
                api_key=settings.STEAM_API_KEY,
                rate_limit_delay=settings.VALVE_RATE_LIMIT_DELAY
            )
        else:
            self.api = OpenDotaAPI(
                rate_limit_delay=settings.OPENDOTA_RATE_LIMIT_DELAY
            )

    async def get_match_history(
        self,
        account_id: int,
        matches_requested: int = 100,
        start_at_match_id: Optional[int] = None
    ) -> List[Dict]:
        """Get match history for a player"""
        return await self.api.get_match_history(
            account_id, matches_requested, start_at_match_id
        )

    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed match information"""
        return await self.api.get_match_details(match_id)

    async def get_heroes(self) -> List[Dict]:
        """Get list of all heroes"""
        return await self.api.get_heroes()

    def normalize_match_data(self, match_data: Dict, account_id: int) -> Dict:
        """Normalize match data from different API providers"""
        return self.api.normalize_match_data(match_data, account_id)
