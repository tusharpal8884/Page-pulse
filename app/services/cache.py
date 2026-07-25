from cachetools import TTLCache
from app.config import settings

class CacheService:
    def __init__(self):
        # Configurable TTL via environment variables
        self._cache = TTLCache(maxsize=1000, ttl=settings.CACHE_TTL_SECONDS)

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value: dict):
        self._cache[key] = value

    def clear(self):
        self._cache.clear()

cache_service = CacheService()