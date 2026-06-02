import os
import time
import asyncio
import logging
from typing import Set, Dict, Any, Callable, Awaitable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class DebouncedFileEventHandler(FileSystemEventHandler):
    def __init__(self, debounce_secs: float, callback: Callable[[str], None]):
        self.debounce_secs = debounce_secs
        self.callback = callback
        self.pending: Dict[str, asyncio.TimerHandle] = {}
        self.loop = asyncio.get_event_loop()

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def _schedule(self, path: str):
        if path in self.pending:
            self.pending[path].cancel()
            
        self.pending[path] = self.loop.call_later(
            self.debounce_secs, 
            self._execute, 
            path
        )

    def _execute(self, path: str):
        if path in self.pending:
            del self.pending[path]
        self.callback(path)

class MemoryIndexer:
    def __init__(self, db_manager, embedding_manager, worksapce_dir: str):
        self.db = db_manager
        self.embeddings = embedding_manager
        self.workspace_dir = worksapce_dir
        self.observer = None
        self.session_delta_threshold_bytes = 64 * 1024
        self.session_delta_threshold_messages = 10
        self.session_state: Dict[str, Dict[str, int]] = {}

    def start_watching(self, debounce_secs: float = 5.0):
        if self.observer:
            return

        def on_file_changed(path: str):
            asyncio.create_task(self.process_file(path))

        handler = DebouncedFileEventHandler(debounce_secs, on_file_changed)
        self.observer = Observer()
        self.observer.schedule(handler, self.workspace_dir, recursive=True)
        self.observer.start()
        logger.info(f"Started watching {self.workspace_dir} for changes.")

    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    async def process_file(self, path: str):
        if not path.endswith('.md') and not path.endswith('.txt'):
            return
            
        try:
            stat = os.stat(path)
            
            # Track sessions specifically
            if "sessions" in path.lower():
                state = self.session_state.get(path, {"size": 0, "messages": 0})
                delta_bytes = stat.st_size - state["size"]
                if delta_bytes < self.session_delta_threshold_bytes:
                    return # Skip indexing until threshold met
                self.session_state[path] = {"size": stat.st_size, "messages": state["messages"] + 1}
                
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            from src.indexing.chunking import compute_sha256, chunk_text
            file_hash = compute_sha256(content)
            
            # Check if unchanged
            conn = self.db.get_connection()
            row = conn.execute("SELECT hash FROM files WHERE path = ?", (path,)).fetchone()
            if row and row["hash"] == file_hash:
                logger.debug(f"Skipping unchanged file: {path}")
                return

            chunks = chunk_text(content)
            
            # Get Embeddings using batching
            texts = [c.text for c in chunks]
            embeddings_list = await self.embeddings.embed_batch(texts)
            
            # Write to DB
            cursor = conn.cursor()
            
            # Clean up old chunks
            cursor.execute("DELETE FROM chunks WHERE path = ?", (path,))
            cursor.execute("DELETE FROM chunks_vec WHERE id IN (SELECT id FROM chunks WHERE path = ?)", (path,))
            cursor.execute("DELETE FROM chunks_fts WHERE path = ?", (path,))
            
            for i, chunk in enumerate(chunks):
                chunk_id = compute_sha256(f"{path}:{chunk.start_line}:{chunk.hash}")
                embedding = embeddings_list[i] if i < len(embeddings_list) else []
                
                import json
                cursor.execute(
                    "INSERT INTO chunks (id, path, source, chunkIndex, content) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, path, "memory", i, chunk.text)
                )
                
                if embedding and len(embedding) > 0:
                    cursor.execute(
                        "INSERT INTO chunks_vec (id, embedding) VALUES (?, ?)",
                        (chunk_id, json.dumps(embedding))
                    )
                
                cursor.execute(
                    "INSERT INTO chunks_fts (id, path, source, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, path, "memory", chunk.text)
                )
                
            cursor.execute(
                """
                INSERT INTO files (path, source, absPath, mtimeMs, size, hash) 
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path, source) DO UPDATE SET
                    hash=excluded.hash,
                    mtimeMs=excluded.mtimeMs,
                    size=excluded.size
                """,
                (path, "memory", path, int(stat.st_mtime * 1000), stat.st_size, file_hash)
            )
            conn.commit()
            logger.info(f"Indexed file: {path} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"Error processing file {path}: {e}")
