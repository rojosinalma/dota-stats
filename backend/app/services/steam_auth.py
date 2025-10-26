import httpx
from typing import Optional, Dict
from urllib.parse import urlencode
from ..config import settings
import re


class SteamAuthService:
    STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
    STEAM_API_URL = "https://api.steampowered.com"

    def __init__(self):
        self.api_key = settings.STEAM_API_KEY
        self.callback_url = settings.STEAM_OPENID_CALLBACK_URL

    def get_login_url(self) -> str:
        """Generate Steam OpenID login URL"""
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": self.callback_url,
            "openid.realm": self.callback_url.rsplit('/', 1)[0],
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        return f"{self.STEAM_OPENID_URL}?{urlencode(params)}"

    async def verify_authentication(self, params: Dict[str, str]) -> Optional[str]:
        """Verify Steam OpenID response and extract Steam ID"""
        # Change mode to check_authentication
        verification_params = dict(params)
        verification_params["openid.mode"] = "check_authentication"

        async with httpx.AsyncClient() as client:
            response = await client.post(self.STEAM_OPENID_URL, data=verification_params)

            if "is_valid:true" in response.text:
                # Extract Steam ID from claimed_id
                claimed_id = params.get("openid.claimed_id", "")
                match = re.search(r"https://steamcommunity.com/openid/id/(\d+)", claimed_id)
                if match:
                    return match.group(1)

        return None

    async def get_player_summaries(self, steam_id: str) -> Optional[Dict]:
        """Get player profile information from Steam API"""
        url = f"{self.STEAM_API_URL}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": self.api_key,
            "steamids": steam_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            players = data.get("response", {}).get("players", [])
            return players[0] if players else None

    @staticmethod
    def steam_id_to_account_id(steam_id: str) -> int:
        """Convert Steam ID 64 to Dota 2 account ID (32-bit)"""
        return int(steam_id) - 76561197960265728

    @staticmethod
    def account_id_to_steam_id(account_id: int) -> str:
        """Convert Dota 2 account ID to Steam ID 64"""
        return str(account_id + 76561197960265728)
