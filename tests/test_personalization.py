import pytest
import tempfile
import os
from src.database.db_manager import MemoryDatabaseManager
from src.memory.personalization import UserPersonalization

def _make_db():
    """Create an in-memory DB with schema for testing."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    db = MemoryDatabaseManager(db_path, vector_enabled=False)
    db.ensure_schema(cache_enabled=False, fts_enabled=False)
    return db, tmpdir

def test_user_personalization():
    db, tmpdir = _make_db()
    up = UserPersonalization(db)
    up.update_fact("name", "Alice")
    up.update_preference("language", "python")
    
    assert up.get_fact("name") == "Alice"
    assert up.get_preference("language") == "python"
    
    ctx = up.get_context_string()
    assert "User Facts:" in ctx
    assert "- name: Alice" in ctx
    assert "User Preferences:" in ctx
    assert "- language: python" in ctx
    
    # Test reload (new instance, same DB)
    up2 = UserPersonalization(db)
    assert up2.get_fact("name") == "Alice"
    db.close()
