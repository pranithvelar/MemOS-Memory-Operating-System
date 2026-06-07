import sqlite3
import sqlite_vec
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

VECTOR_TABLE = "chunks_vec"
FTS_TABLE = "chunks_fts"
EMBEDDING_CACHE_TABLE = "embedding_cache"

class MemoryDatabaseManager:
    def __init__(self, db_path: str, vector_enabled: bool = True):
        self.db_path = db_path
        self.vector_enabled = vector_enabled
        self.conn = self._open_database()
        
    def _open_database(self) -> sqlite3.Connection:
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Configure WAL and busy timeout
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        
        if self.vector_enabled:
            # Enable sqlite-vec
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            logger.info("Loaded sqlite-vec extension successfully.")
        
        return conn

    def close(self):
        if self.conn:
            # Optimize WAL before closing if needed, though PRAGMA wal_checkpoint(TRUNCATE) helps.
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.conn.close()

    def ensure_vector_table(self, dimensions: int):
        if not self.vector_enabled:
            return
            
        self.conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {VECTOR_TABLE} USING vec0(
                id TEXT PRIMARY KEY,
                embedding FLOAT[{dimensions}]
            )
            """
        )
        self.conn.commit()
        
    def drop_vector_table(self):
        try:
            self.conn.execute(f"DROP TABLE IF EXISTS {VECTOR_TABLE}")
            self.conn.commit()
        except sqlite3.Error as e:
            logger.debug(f"Failed to drop {VECTOR_TABLE}: {e}")

    def ensure_schema(self, cache_enabled: bool = True, fts_enabled: bool = True):
        cursor = self.conn.cursor()
        
        # Meta table for storing index versions and tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        
        # Files table for sync-ops tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                path TEXT NOT NULL,
                source TEXT NOT NULL,
                absPath TEXT NOT NULL,
                mtimeMs INTEGER NOT NULL,
                size INTEGER NOT NULL,
                hash TEXT NOT NULL,
                PRIMARY KEY (path, source)
            )
            """
        )
        
        # Chunks table mapping chunk entries to files
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                source TEXT NOT NULL,
                chunkIndex INTEGER NOT NULL,
                content TEXT NOT NULL
            )
            """
        )
        
        # ── NEW: Calendar/temporal facts (replaces facts.json) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                date_start TEXT NOT NULL,
                date_end TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                confidence REAL DEFAULT 1.0,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                reminder_sent TEXT DEFAULT NULL
            )
            """
        )
        # Safe migration: add reminder_sent to existing databases that predate this column
        try:
            cursor.execute("ALTER TABLE facts ADD COLUMN reminder_sent TEXT DEFAULT NULL")
            self.conn.commit()
        except Exception:
            pass  # Column already exists — no-op

        # ── NEW: Short-term recall tracking (replaces short-term-recall.json) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS short_term_recall (
                key TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                start_line INTEGER DEFAULT 0,
                end_line INTEGER DEFAULT 0,
                source TEXT NOT NULL,
                snippet TEXT,
                recall_count INTEGER DEFAULT 0,
                daily_count INTEGER DEFAULT 0,
                grounded_count INTEGER DEFAULT 0,
                total_score REAL DEFAULT 0,
                max_score REAL DEFAULT 0,
                first_recalled_at TEXT,
                last_recalled_at TEXT,
                query_hashes TEXT DEFAULT '[]',
                recall_days TEXT DEFAULT '[]',
                concept_tags TEXT DEFAULT '[]',
                claim_hash TEXT,
                promoted_at TEXT
            )
            """
        )

        # ── NEW: User profile (replaces user_profile.json) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT NOT NULL,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (key, category)
            )
            """
        )

        # ── NEW: Session messages (replaces *.jsonl files) ──
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_sid ON sessions(session_id)"
        )

        # Embedding cache table
        if cache_enabled:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {EMBEDDING_CACHE_TABLE} (
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider_key TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    dims INTEGER,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (provider, model, provider_key, hash)
                )
                """
            )
            
        # FTS table
        if fts_enabled:
            cursor.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE} USING fts5(
                    id UNINDEXED,
                    path UNINDEXED,
                    source UNINDEXED,
                    content,
                    tokenize='porter'
                )
                """
            )
            
        self.conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        return self.conn
