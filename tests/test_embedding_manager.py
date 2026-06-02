import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.embeddings.embedding_manager import EmbeddingManager, EmbeddingProviderError

@pytest.fixture
def mock_db_manager():
    manager = MagicMock()
    conn = MagicMock()
    manager.get_connection.return_value = conn
    conn.execute.return_value.fetchall.return_value = []
    return manager

@pytest.mark.asyncio
async def test_embed_batch_uses_cache(mock_db_manager):
    import json
    
    # Mock cache hit
    mock_db_manager.get_connection().execute().fetchall.return_value = [
        {"hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "embedding": json.dumps([0.1] * 768)}
    ]
    
    manager = EmbeddingManager(db_manager=mock_db_manager)
    
    # Empty string hashes to e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    res = await manager.embed_batch([""])
    assert len(res) == 1
    assert len(res[0]) == 768
    assert res[0][0] == 0.1

@pytest.mark.asyncio
@patch('ollama.AsyncClient')
async def test_embed_dimension_mismatch(mock_client_class, mock_db_manager):
    # Setup mock to return wrong dimensions
    mock_instance = AsyncMock()
    mock_instance.embeddings.return_value = {"embedding": [0.5, 0.5]}  # only 2 dims
    mock_client_class.return_value = mock_instance
    
    manager = EmbeddingManager(db_manager=mock_db_manager, max_retries=1, base_delay=0)
    
    with pytest.raises(EmbeddingProviderError, match="Dimension mismatch"):
        await manager.embed_query("test text")

@pytest.mark.asyncio
@patch('ollama.AsyncClient')
async def test_embed_single_success(mock_client_class, mock_db_manager):
    # Setup mock
    mock_instance = AsyncMock()
    mock_instance.embeddings.return_value = {"embedding": [0.1] * 768}
    mock_client_class.return_value = mock_instance
    
    manager = EmbeddingManager(db_manager=mock_db_manager)
    res = await manager.embed_query("test")
    assert len(res) == 768
