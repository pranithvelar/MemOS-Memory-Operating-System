import pytest
from src.search.hybrid_search import HybridSearcher, HybridSearchResult
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_hybrid_search_scoring():
    mock_db = MagicMock()
    mock_embed = MagicMock()
    mock_embed.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    
    searcher = HybridSearcher(mock_db, mock_embed)
    
    # Mock vector/keyword fetches
    searcher.search_vector = AsyncMock(return_value={
        "chunk_1": HybridSearchResult("chunk_1", "/doc.md", "memory", "hello", 1, 1, vector_score=0.9),
        "chunk_2": HybridSearchResult("chunk_2", "/doc2.md", "memory", "world", 1, 1, vector_score=0.6)
    })
    searcher.search_keyword = AsyncMock(return_value={
        "chunk_1": HybridSearchResult("chunk_1", "/doc.md", "memory", "hello", 1, 1, text_score=0.8),
        "chunk_3": HybridSearchResult("chunk_3", "/doc3.md", "memory", "test", 1, 1, text_score=0.9)
    })
    
    results = await searcher.search("hello", vector_weight=0.7, text_weight=0.3, min_score=0.5, max_results=10)
    
    assert len(results) == 1 # chunk_1: 0.9*0.7 + 0.8*0.3 = 0.87 (kept); chunk_2: 0.42 (eliminated); chunk_3: 0.27 (eliminated)
    # chunk_1: 0.9*0.7 + 0.8*0.3 = 0.63 + 0.24 = 0.87 (kept)
    # chunk_2: 0.6*0.7 + 0.0*0.3 = 0.42 (eliminated if min_score is 0.5)
    # chunk_3: 0.0*0.7 + 0.9*0.3 = 0.27 (eliminated)
    
    assert results[0].chunk_id == "chunk_1"
    assert round(results[0].score, 2) == 0.87

@pytest.mark.asyncio
async def test_hybrid_search_type_coercion():
    mock_db = MagicMock()
    mock_embed = MagicMock()
    mock_embed.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    
    searcher = HybridSearcher(mock_db, mock_embed)
    
    searcher.search_vector = AsyncMock(return_value={
        "chunk_1": HybridSearchResult("chunk_1", "/doc.md", "memory", "hello", 1, 1, vector_score=0.9)
    })
    searcher.search_keyword = AsyncMock(return_value={})
    
    # Pass strings for float/int arguments
    results = await searcher.search(
        "hello", 
        vector_weight="0.7", 
        text_weight="0.3", 
        min_score="0.5", 
        max_results="5"
    )
    
    assert len(results) == 1
    assert results[0].chunk_id == "chunk_1"
