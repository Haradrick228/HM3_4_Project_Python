import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cache import RedisCache

class TestRedisCache:
    # Тесты функциональности Redis кэша

    @patch('src.cache.redis.Redis')
    def test_cache_get_success(self, mock_redis):
        # Тест успешного получения из кэша
        mock_client = MagicMock()
        mock_client.get.return_value = '{"key": "value"}'
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.get("test_key")

        assert result == {"key": "value"}
        mock_client.get.assert_called_once_with("test_key")

    @patch('src.cache.redis.Redis')
    def test_cache_get_none(self, mock_redis):
        # Тест получения из кэша когда значения нет
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.get("nonexistent")

        assert result is None

    @patch('src.cache.redis.Redis')
    def test_cache_get_exception(self, mock_redis):
        # Тест получения из кэша с исключением
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.get("test_key")

        assert result is None

    @patch('src.cache.redis.Redis')
    def test_cache_set_success(self, mock_redis):
        # Тест успешной установки в кэш
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        mock_client.setex.assert_called_once()

    @patch('src.cache.redis.Redis')
    def test_cache_set_default_ttl(self, mock_redis):
        # Тест установки в кэш с TTL по умолчанию
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", {"data": "value"})

        assert result is True

    @patch('src.cache.redis.Redis')
    def test_cache_set_exception(self, mock_redis):
        # Тест установки в кэш с исключением
        mock_client = MagicMock()
        mock_client.setex.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", {"data": "value"})

        assert result is False

    @patch('src.cache.redis.Redis')
    def test_cache_delete_success(self, mock_redis):
        # Тест успешного удаления из кэша
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    @patch('src.cache.redis.Redis')
    def test_cache_delete_exception(self, mock_redis):
        # Тест удаления из кэша с исключением
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.delete("test_key")

        assert result is False

    @patch('src.cache.redis.Redis')
    def test_cache_increment_success(self, mock_redis):
        # Тест успешного инкремента счетчика
        mock_client = MagicMock()
        mock_client.incr.return_value = 5
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.increment("counter")

        assert result == 5
        mock_client.incr.assert_called_once_with("counter")

    @patch('src.cache.redis.Redis')
    def test_cache_increment_exception(self, mock_redis):
        # Тест инкремента счетчика с исключением
        mock_client = MagicMock()
        mock_client.incr.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        cache = RedisCache()
        result = cache.increment("counter")

        assert result == 0
