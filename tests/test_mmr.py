import pytest
from src.search.mmr import tokenize, jaccard_similarity, MMRConfig, apply_mmr_to_hybrid_results
from src.search.hybrid_search import HybridSearchResult

def test_tokenize():
    tokens = tokenize("Hello world 这是一段测试 text")
    assert "hello" in tokens
    assert "world" in tokens
    assert "text" in tokens
    # CJK unigrams and bigrams should be extracted
    
def test_jaccard_similarity():
    # disjoint
    assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
    # identical
    assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
    # partial
    assert jaccard_similarity({"a", "b"}, {"b", "c"}) == 1/3
    
def test_apply_mmr():
    r1 = HybridSearchResult("1", "path1", "memory", "The quick brown fox", 1, 1)
    r1.score = 0.9
    r2 = HybridSearchResult("2", "path2", "memory", "The quick brown fox jumps", 1, 1)
    r2.score = 0.8
    r3 = HybridSearchResult("3", "path3", "memory", "A completely different topic about AI", 1, 1)
    r3.score = 0.7
    
    # Without MMR
    # r1 (0.9), r2 (0.8), r3 (0.7)
    
    config = MMRConfig(enabled=True, lambda_param=0.5)
    reranked = apply_mmr_to_hybrid_results([r1, r2, r3], config)
    
    # With MMR (lambda=0.5), r1 should be chosen first. 
    # Next, r2 has high similarity to r1, so its MMR score drops heavily.
    # r3 has 0 similarity to r1, so its MMR score is purely relevance.
    # r3 should be chosen second!
    
    assert reranked[0].chunk_id == "1"
    assert reranked[1].chunk_id == "3"
    assert reranked[2].chunk_id == "2"
