import pytest
from src.indexing.chunking import chunk_text, compute_sha256

def test_chunk_text():
    text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
    chunks = chunk_text(text, max_tokens=10, overlap=5)
    
    # Expecting sentences to be split based on the artificial token limit of 10
    # tokens ~ words * 1.3
    # "This is sentence one." -> 4 words = 5.2 tokens.
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.hash, str)
        assert len(chunk.hash) == 64

def test_compute_sha256():
    assert compute_sha256("test") == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
