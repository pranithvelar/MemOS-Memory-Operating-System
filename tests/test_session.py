import pytest
import tempfile
import os
from src.database.db_manager import MemoryDatabaseManager
from src.agent.session import SessionManager

def _make_db():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    db = MemoryDatabaseManager(db_path, vector_enabled=False)
    db.ensure_schema(cache_enabled=False, fts_enabled=False)
    return db, tmpdir

def test_session_manager():
    db, tmpdir = _make_db()
    sm = SessionManager(db)
    sm.append_message("session_1", "user", "Hello there")
    sm.append_message("session_1", "assistant", "Hi, how can I help?")
    
    sm.append_message("session_2", "user", "Different context")
    
    history1 = sm.load_session("session_1")
    assert len(history1) == 2
    assert history1[0]["role"] == "user"
    assert history1[1]["content"] == "Hi, how can I help?"
    
    history2 = sm.load_session("session_2")
    assert len(history2) == 1
    
    sm.clear_session("session_1")
    assert len(sm.load_session("session_1")) == 0
    db.close()
