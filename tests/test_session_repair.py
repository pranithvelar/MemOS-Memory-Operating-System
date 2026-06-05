"""
Tests for session transcript repair and multi-stage compaction.

Covers:
  - Orphaned tool result removal
  - Orphaned tool call patching (synthetic failure injection)
  - Malformed JSON repair in tool call blocks
  - Consecutive same-role message merging
  - Session write-lock concurrency
  - Multi-stage compaction fallback (Stage 1, 2, 3)
  - Identifier preservation extraction
  - Session overwrite after repair
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.session_transcript_repair import (
    repair_tool_use_result_pairing,
    extract_identifiers,
    _message_has_tool_call,
    _message_is_tool_result,
    _try_fix_json_in_content,
)
from src.agent.session import SessionManager
from src.agent.loop import AgentLoop
from src.database.db_manager import MemoryDatabaseManager


# ---------------------------------------------------------------------------
# Helper: make a temp DB
# ---------------------------------------------------------------------------
def _make_db():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_repair.db")
    db = MemoryDatabaseManager(db_path, vector_enabled=False)
    db.ensure_schema(cache_enabled=False, fts_enabled=False)
    return db, tmpdir


# ===========================================================================
# Tests for session_transcript_repair.py
# ===========================================================================

class TestToolCallDetection:
    def test_detects_fenced_json_tool_call(self):
        msg = {"role": "assistant", "content": '```json\n{"name": "search_memory", "arguments": {"query": "test"}}\n```'}
        assert _message_has_tool_call(msg)

    def test_detects_bare_json_tool_call(self):
        msg = {"role": "assistant", "content": 'I will search.\n{"name": "save_note", "arguments": {"text": "hello"}}'}
        assert _message_has_tool_call(msg)

    def test_no_tool_call_in_normal_text(self):
        msg = {"role": "assistant", "content": "Hello! How can I help you today?"}
        assert not _message_has_tool_call(msg)

    def test_empty_content(self):
        msg = {"role": "assistant", "content": ""}
        assert not _message_has_tool_call(msg)


class TestToolResultDetection:
    def test_detects_result_prefix(self):
        msg = {"role": "user", "content": "Result: Successfully saved note."}
        assert _message_is_tool_result(msg)

    def test_result_prefix_case_insensitive(self):
        msg = {"role": "user", "content": "result: Tool search_memory failed: timeout"}
        assert _message_is_tool_result(msg)

    def test_normal_user_message_is_not_result(self):
        msg = {"role": "user", "content": "What's the weather today?"}
        assert not _message_is_tool_result(msg)


class TestJSONRepair:
    def test_fixes_unquoted_keys(self):
        # The repair function targets blocks that already have "name" quoted
        # but have other unquoted keys (e.g., arguments)
        content = '```json\n{"name": "search_memory", arguments: {"query": "test"}}\n```'
        fixed = _try_fix_json_in_content(content)
        assert '"arguments"' in fixed

    def test_preserves_valid_json(self):
        content = '```json\n{"name": "search_memory", "arguments": {"query": "test"}}\n```'
        fixed = _try_fix_json_in_content(content)
        assert fixed == content


class TestRepairToolUsePairing:
    def test_clean_transcript_no_changes(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "Thanks"},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert not report["repaired"]
        assert len(report["messages"]) == 3

    def test_orphaned_tool_result_dropped(self):
        """Tool result without a preceding tool call should be dropped."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "Result: Tool search_memory returned: nothing found"},
            {"role": "assistant", "content": "I couldn't find anything."},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert report["repaired"]
        assert report["stats"]["orphaned_results_dropped"] == 1
        # The orphaned result should be gone
        assert len(report["messages"]) == 2
        assert all("Result:" not in m.get("content", "") for m in report["messages"] if m["role"] == "user")

    def test_orphaned_tool_call_patched(self):
        """Tool call without a following result should get a synthetic failure."""
        messages = [
            {"role": "user", "content": "Search for my notes"},
            {"role": "assistant", "content": '```json\n{"name": "search_memory", "arguments": {"query": "notes"}}\n```'},
            {"role": "user", "content": "Anything else?"},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert report["repaired"]
        assert report["stats"]["orphaned_calls_patched"] == 1
        # Should inject a synthetic failure between the tool call and next user msg
        repaired = report["messages"]
        # Find the injected message
        injected = [m for m in repaired if "interrupted" in m.get("content", "").lower()]
        assert len(injected) == 1

    def test_trailing_tool_call_patched(self):
        """Tool call at the very end of the transcript should get a synthetic failure."""
        messages = [
            {"role": "user", "content": "Save this note"},
            {"role": "assistant", "content": '```json\n{"name": "save_note", "arguments": {"text": "hello"}}\n```'},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert report["repaired"]
        assert report["stats"]["orphaned_calls_patched"] == 1
        assert len(report["messages"]) == 3  # user + assistant + injected result

    def test_properly_paired_tool_use_untouched(self):
        """A proper tool call → result pair should not be modified."""
        messages = [
            {"role": "user", "content": "Search memory"},
            {"role": "assistant", "content": '```json\n{"name": "search_memory", "arguments": {"query": "test"}}\n```'},
            {"role": "user", "content": "Result: Found 2 matches."},
            {"role": "assistant", "content": "I found 2 results."},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert not report["repaired"]
        assert len(report["messages"]) == 4

    def test_consecutive_role_merge(self):
        """Two consecutive user messages should be merged."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "Also, what time is it?"},
            {"role": "assistant", "content": "Hi! It's 3 PM."},
        ]
        report = repair_tool_use_result_pairing(messages)
        assert report["repaired"]
        assert report["stats"]["consecutive_roles_merged"] == 1
        assert len(report["messages"]) == 2

    def test_empty_messages(self):
        report = repair_tool_use_result_pairing([])
        assert not report["repaired"]
        assert report["messages"] == []


class TestIdentifierExtraction:
    def test_extracts_uuid(self):
        text = "The job ID is 550e8400-e29b-41d4-a716-446655440000"
        ids = extract_identifiers(text)
        assert "550e8400-e29b-41d4-a716-446655440000" in ids

    def test_extracts_ipv4(self):
        text = "Connect to 192.168.1.100:8080 for the API"
        ids = extract_identifiers(text)
        assert any("192.168.1.100" in i for i in ids)

    def test_extracts_url(self):
        text = "See https://example.com/api/v2/docs for details"
        ids = extract_identifiers(text)
        assert any("https://example.com" in i for i in ids)

    def test_extracts_file_path(self):
        text = "The config is at /etc/nginx/conf.d/default.conf"
        ids = extract_identifiers(text)
        assert any("/etc/nginx" in i for i in ids)

    def test_no_identifiers_in_plain_text(self):
        text = "Hello, how are you today?"
        ids = extract_identifiers(text)
        assert len(ids) == 0


# ===========================================================================
# Tests for session.py (write-lock + repair on load)
# ===========================================================================

class TestSessionManagerRepair:
    def test_repair_on_load(self):
        """Loading a session with orphaned results should auto-repair."""
        db, tmpdir = _make_db()
        sm = SessionManager(db)

        # Insert messages with an orphaned tool result
        sm.append_message("test_repair", "user", "Hello")
        sm.append_message("test_repair", "user", "Result: some orphaned result")
        sm.append_message("test_repair", "assistant", "Hi there")

        # Load should auto-repair
        history = sm.load_session("test_repair")
        # The orphaned result should have been dropped
        assert len(history) == 2
        assert all("Result:" not in m.get("content", "") for m in history if m["role"] == "user")
        db.close()

    def test_overwrite_session(self):
        """overwrite_session should replace the full session history."""
        db, tmpdir = _make_db()
        sm = SessionManager(db)

        sm.append_message("test_ow", "user", "old message 1")
        sm.append_message("test_ow", "assistant", "old message 2")

        sm.overwrite_session("test_ow", [
            {"role": "user", "content": "new message 1"},
            {"role": "assistant", "content": "new message 2"},
            {"role": "user", "content": "new message 3"},
        ])

        # Reload raw (bypass repair)
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT role, content FROM sessions WHERE session_id = ? ORDER BY id",
            ("test_ow",)
        ).fetchall()
        assert len(rows) == 3
        assert rows[0]["content"] == "new message 1"
        db.close()

    def test_lock_creation(self):
        """Each session_id should get its own lock."""
        db, tmpdir = _make_db()
        sm = SessionManager(db)

        lock1 = sm.get_lock("session_a")
        lock2 = sm.get_lock("session_b")
        lock1_again = sm.get_lock("session_a")

        assert lock1 is lock1_again  # Same session -> same lock
        assert lock1 is not lock2    # Different session -> different lock
        assert isinstance(lock1, asyncio.Lock)
        db.close()


# ===========================================================================
# Tests for multi-stage compaction (loop.py)
# ===========================================================================

class TestMultiStageCompaction:
    def test_stage3_hard_fallback_never_crashes(self):
        """Stage 3 should return a string no matter what."""
        loop = AgentLoop()
        messages = [
            {"role": "user", "content": "x" * 5000},
            {"role": "assistant", "content": "y" * 5000},
            {"role": "user", "content": "z" * 5000},
        ]
        result = loop._stage3_hard_fallback(messages)
        assert isinstance(result, str)
        assert "3 messages" in result
        assert "oversized" in result

    def test_stage3_with_no_oversized(self):
        """Stage 3 with small messages should report 0 oversized."""
        loop = AgentLoop()
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        result = loop._stage3_hard_fallback(messages)
        assert "2 messages" in result
        assert "0 oversized" in result

    @pytest.mark.asyncio
    async def test_compaction_skips_when_under_threshold(self):
        """Compaction should not run if uncompacted messages < threshold."""
        loop = AgentLoop()
        loop._history = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
        loop._compacted_up_to = 0
        # Should silently do nothing (threshold is 20)
        await loop._maybe_compact()
        assert loop._compacted_up_to == 0  # No change


# ===========================================================================
# Concurrency stress test
# ===========================================================================

@pytest.mark.asyncio
async def test_concurrent_lock_acquisition():
    """Multiple coroutines acquiring the same session lock should serialize."""
    db, tmpdir = _make_db()
    sm = SessionManager(db)
    lock = sm.get_lock("concurrent_test")

    order = []

    async def worker(worker_id, delay):
        async with lock:
            order.append(f"start_{worker_id}")
            await asyncio.sleep(delay)
            order.append(f"end_{worker_id}")

    # Launch 3 workers concurrently
    await asyncio.gather(
        worker("a", 0.05),
        worker("b", 0.05),
        worker("c", 0.05),
    )

    # Verify serialized execution: each worker must start after the previous ends
    # The order should be interleaved as: start_X, end_X, start_Y, end_Y, ...
    for i in range(0, len(order), 2):
        assert order[i].startswith("start_")
        assert order[i+1].startswith("end_")
        # Both should reference the same worker
        worker_start = order[i].split("_")[1]
        worker_end = order[i+1].split("_")[1]
        assert worker_start == worker_end

    db.close()
