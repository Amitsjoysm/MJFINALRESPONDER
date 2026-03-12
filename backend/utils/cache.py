"""Caching layer for performance optimization"""
from typing import Any, Optional, Callable
from functools import wraps
import json
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Simple in-memory cache (use Redis in production)"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            # Check expiry
            if key in self._expiry:
                if datetime.now() > self._expiry[key]:
                    # Expired
                    del self._cache[key]
                    del self._expiry[key]
                    return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        self._cache[key] = value
        if ttl > 0:
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def delete(self, key: str):
        """Delete from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._expiry.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.delete(key)

# Global cache instance
cache_service = CacheService()

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached = cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cache miss: {func.__name__}")
            
            return result
        return wrapper
    return decorator
