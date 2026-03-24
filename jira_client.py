"""HTTP client for Jira Cloud REST API v3."""

import asyncio
import time

import httpx

from config import settings


class JiraCloudClient:
    """Async HTTP client with rate-limit handling for Jira Cloud."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_remaining: int = 100
        self._rate_limit_reset: float = 0

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=(settings.jira_email, settings.jira_api_token),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                verify=settings.jira_ssl_verify,
                timeout=30.0,
            )
        return self._client

    async def _handle_rate_limit(self, resp: httpx.Response):
        """Track rate limit headers and back off if needed."""
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None:
            self._rate_limit_remaining = int(remaining)
        reset = resp.headers.get("Retry-After")
        if resp.status_code == 429:
            wait = int(reset) if reset else 5
            await asyncio.sleep(wait)
            return True  # Should retry
        return False

    # --- Core HTTP methods ---

    async def get(self, path: str, api: str = "v3", **params) -> dict | list:
        base = settings.api_v3_url if api == "v3" else settings.api_v2_url
        url = f"{base}{path}"
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        for attempt in range(3):
            resp = await self.client.get(url, params=params)
            if await self._handle_rate_limit(resp):
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()

    async def post(self, path: str, body: dict, api: str = "v3") -> dict:
        base = settings.api_v3_url if api == "v3" else settings.api_v2_url
        url = f"{base}{path}"
        for attempt in range(3):
            resp = await self.client.post(url, json=body)
            if await self._handle_rate_limit(resp):
                continue
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        resp.raise_for_status()

    async def put(self, path: str, body: dict, api: str = "v3") -> dict:
        base = settings.api_v3_url if api == "v3" else settings.api_v2_url
        url = f"{base}{path}"
        for attempt in range(3):
            resp = await self.client.put(url, json=body)
            if await self._handle_rate_limit(resp):
                continue
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        resp.raise_for_status()

    async def delete(self, path: str, api: str = "v3") -> bool:
        base = settings.api_v3_url if api == "v3" else settings.api_v2_url
        url = f"{base}{path}"
        for attempt in range(3):
            resp = await self.client.delete(url)
            if await self._handle_rate_limit(resp):
                continue
            resp.raise_for_status()
            return True
        resp.raise_for_status()

    # --- Convenience for raw URLs (non-standard API paths) ---

    async def raw_get(self, url: str, **params) -> dict | list:
        full_url = f"{settings.jira_url.rstrip('/')}{url}"
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        resp = await self.client.get(full_url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def raw_post(self, url: str, body: dict) -> dict:
        full_url = f"{settings.jira_url.rstrip('/')}{url}"
        resp = await self.client.post(full_url, json=body)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    async def raw_put(self, url: str, body: dict) -> dict:
        full_url = f"{settings.jira_url.rstrip('/')}{url}"
        resp = await self.client.put(full_url, json=body)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    async def raw_delete(self, url: str) -> bool:
        full_url = f"{settings.jira_url.rstrip('/')}{url}"
        resp = await self.client.delete(full_url)
        resp.raise_for_status()
        return True

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


jira = JiraCloudClient()
