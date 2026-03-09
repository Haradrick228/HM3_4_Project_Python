import redis
import json
from typing import Optional, Any
from .config import settings

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        # Получение значения из кэша
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        # Установка значения в кэш с TTL
        try:
            if ttl is None:
                ttl = settings.CACHE_TTL
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        # Удаление ключа из кэша
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False

    def increment(self, key: str) -> int:
        # Инкремент счетчика
        try:
            return self.redis_client.incr(key)
        except Exception:
            return 0

cache = RedisCache()
