"""Connection pool manager for external services"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HTTPClientPool:
    """HTTP client pool for external API calls"""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                )
            )
            logger.info("HTTP client pool initialized")
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("HTTP client pool closed")

# Global HTTP client pool
http_client_pool = HTTPClientPool()
