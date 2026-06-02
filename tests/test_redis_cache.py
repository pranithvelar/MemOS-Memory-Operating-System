import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.cache.redis_client import RedisManager
from src.cache.embedding_cache_redis import RedisEmbeddingCache
from src.cache.search_cache_redis import RedisSearchCache
from src.search.hybrid_search import HybridSearchResult

@pytest.mark.asyncio
async def test_redis_graceful_fallback():
    """If Redis is forced to fail, the manager must politely decline with no exceptions."""
    mgr = RedisManager()
    
    # Force mock a failure by disabling it
    with patch.object(mgr, 'enabled', False):
        client = await mgr.get_client()
        assert client is None

@pytest.mark.asyncio
async def test_search_cache_empty_when_disabled():
    cache = RedisSearchCache()
    # Force it offline
    with patch.object(cache.redis_mgr, 'get_client', return_value=None):
        res = await cache.get_search_results("fake query", ["memory"])
        assert res is None

@pytest.mark.asyncio
async def test_embedding_cache_empty_when_disabled():
    cache = RedisEmbeddingCache()
    with patch.object(cache.redis_mgr, 'get_client', return_value=None):
        res = await cache.get_embeddings("ollama", "model", ["hash123"])
        assert res == {}
