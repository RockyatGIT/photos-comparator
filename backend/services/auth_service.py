import time
from urllib.parse import urlencode
from typing import Optional, Dict, Any, Tuple
import httpx

from ..core.config import settings
from ..repositories.account_repo import AccountRepository

class AuthService:
    def __init__(self, account_repo: AccountRepository = AccountRepository):
        self.account_repo = account_repo

    def get_auth_url(self, account_id: int) -> str:
        client_id = settings.get_client_id()
        if not client_id:
            raise ValueError("Google Client ID is not configured. Please enter your Client ID in the app settings.")

        params = {
            "client_id": client_id,
            "redirect_uri": settings.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(settings.SCOPES),
            "access_type": "offline",
            "prompt": "consent select_account",
            "state": f"account_{account_id}",
        }
        return f"{settings.AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, account_id: int) -> Dict[str, Any]:
        client_id = settings.get_client_id()
        client_secret = settings.get_client_secret()
        if not client_id or not client_secret:
            raise ValueError("Google OAuth credentials are not fully configured.")

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            payload = {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            res = await client.post(settings.TOKEN_URL, data=payload)
            res.raise_for_status()
            token_data = res.json()

            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", settings.DEFAULT_TOKEN_EXPIRY_SECONDS)
            expires_at = time.time() + expires_in

            user_info = await self.fetch_user_info(access_token)
            email = user_info.get("email", f"account{account_id}@gmail.com")
            name = user_info.get("name", f"Account {account_id}")
            picture = user_info.get("picture", "")

            self.account_repo.save_token(
                account_id=account_id,
                email=email,
                name=name,
                picture=picture,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

            return {
                "account_id": account_id,
                "email": email,
                "name": name,
                "picture": picture,
            }

    async def refresh_access_token(self, account_id: int) -> Optional[str]:
        account = self.account_repo.get(account_id)
        if not account or not account.get("refresh_token"):
            return None

        client_id = settings.get_client_id()
        client_secret = settings.get_client_secret()
        if not client_id or not client_secret:
            return None

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": account["refresh_token"],
                "grant_type": "refresh_token",
            }
            res = await client.post(settings.TOKEN_URL, data=payload)
            if res.status_code != 200:
                print(f"Failed to refresh token for account {account_id}: {res.text}")
                return None

            data = res.json()
            new_access_token = data["access_token"]
            expires_in = data.get("expires_in", settings.DEFAULT_TOKEN_EXPIRY_SECONDS)
            expires_at = time.time() + expires_in

            self.account_repo.save_token(
                account_id=account_id,
                email=account["email"],
                name=account["name"],
                picture=account["picture"],
                access_token=new_access_token,
                refresh_token=account["refresh_token"],
                expires_at=expires_at,
            )
            return new_access_token

    async def get_valid_token(self, account_id: int) -> Optional[str]:
        account = self.account_repo.get(account_id)
        if not account:
            return None

        # If token expires within refresh buffer, refresh
        if account["expires_at"] and time.time() > (account["expires_at"] - settings.TOKEN_REFRESH_BUFFER_SECONDS):
            return await self.refresh_access_token(account_id)

        return account.get("access_token")

    async def fetch_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.USERINFO_TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            res = await client.get(settings.USERINFO_URL, headers=headers)
            res.raise_for_status()
            return res.json()

    def disconnect(self, account_id: int) -> None:
        self.account_repo.remove(account_id)

auth_service = AuthService()
