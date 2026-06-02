import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Handles saving and loading of conversational session history.
    Backed by the 'sessions' SQLite table.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        # Keep a reference for summary path compat
        # (loop.py uses session_manager.sessions_dir for summary file path)
        self.sessions_dir = ""

    def _conn(self):
        return self.db.get_connection()

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT role, content, tool_calls FROM sessions WHERE session_id = ? ORDER BY id",
            (session_id,)
        ).fetchall()
        
        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_calls"]:
                try:
                    msg["tool_calls"] = json.loads(row["tool_calls"])
                except Exception:
                    pass
            messages.append(msg)
        return messages

    def append_message(self, session_id: str, role: str, content: str, tool_calls: Any = None):
        conn = self._conn()
        tc_str = json.dumps(tool_calls) if tool_calls is not None else None
        conn.execute(
            "INSERT INTO sessions (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (session_id, role, content, tc_str)
        )
        conn.commit()

    def clear_session(self, session_id: str):
        conn = self._conn()
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
