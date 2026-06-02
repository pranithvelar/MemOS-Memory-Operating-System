import pytest
import tempfile
import os
import json
from src.database.db_manager import MemoryDatabaseManager
from src.memory.short_term import ShortTermMemoryTracker, derive_concept_tags, hash_query, build_claim_hash
from src.search.hybrid_search import HybridSearchResult

def _make_db():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    db = MemoryDatabaseManager(db_path, vector_enabled=False)
    db.ensure_schema(cache_enabled=False, fts_enabled=False)
    return db, tmpdir

def test_derive_concept_tags():
    tags = derive_concept_tags("docs/readme.md", "This is an important concept about python programming")
    assert "readme.md" in tags
    assert "important" in tags
    assert "concept" in tags
    assert "python" in tags
    assert "programming" in tags
    assert "this" not in tags  # stop words
    assert "is" not in tags

def test_hash_query():
    assert hash_query("hello world") == hash_query("Hello WORLD ")
    assert len(hash_query("test")) == 12

def test_build_claim_hash():
    s1 = "This  has    many   spaces"
    s2 = "This has many spaces"
    assert build_claim_hash(s1) == build_claim_hash(s2)

def test_track_recalls():
    db, tmpdir = _make_db()
    tracker = ShortTermMemoryTracker(db)
    
    r1 = HybridSearchResult("chunk1", "/foo/bar.md", "memory", "Snippet text", 10, 15)
    r1.score = 0.8
    
    tracker.track_recalls([r1], "lookup query")
    
    # Verify via DB
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM short_term_recall").fetchall()
    assert len(rows) == 1
    
    entry = dict(rows[0])
    assert entry["recall_count"] == 1
    assert entry["daily_count"] == 1
    assert entry["max_score"] == 0.8
    assert entry["source"] == "memory"
    
    # Track again, should update count
    r2 = HybridSearchResult("chunk1", "/foo/bar.md", "memory", "Snippet text", 10, 15)
    r2.score = 0.95
    tracker.track_recalls([r2], "lookup query 2")
    
    rows = conn.execute("SELECT * FROM short_term_recall").fetchall()
    assert len(rows) == 1
    
    entry = dict(rows[0])
    assert entry["recall_count"] == 2
    assert entry["max_score"] == 0.95
    query_hashes = json.loads(entry["query_hashes"])
    assert len(query_hashes) == 2
    db.close()
