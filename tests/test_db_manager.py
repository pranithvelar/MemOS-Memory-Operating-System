import pytest
import tempfile
import os
from src.database.db_manager import MemoryDatabaseManager

def test_memory_database_manager_initialization():
    with tempfile.TemporaryDirectory() as tempdir:
        db_path = os.path.join(tempdir, "memory.db")
        manager = MemoryDatabaseManager(db_path=db_path, vector_enabled=True)
        
        assert os.path.exists(db_path)
        
        conn = manager.get_connection()
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal_mode.lower() == "wal"
        
        # Test schema generation
        manager.ensure_schema()
        
        # Test vector virtual table
        manager.ensure_vector_table(768)
        
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        assert "files" in table_names
        assert "chunks" in table_names
        assert "embedding_cache" in table_names
        
        manager.close()
