"""
Tests all 3 alert windows: 1h, 15m, and exact-time (NOW).
Injects synthetic events at exactly those offsets and confirms each fires once and only once.
"""
import asyncio
import os
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from src.config.settings import IntelligentMemoryConfig
from src.database.db_manager import MemoryDatabaseManager
from BACKGROUND_WORKER.proactive_events import ProactiveEventsWatcher

async def main():
    config = IntelligentMemoryConfig.load()
    db = MemoryDatabaseManager(os.path.join(config.workspace_dir, "memory.db"))
    conn = db.get_connection()

    now = datetime.now(timezone.utc)

    # Clean up any previous test rows
    conn.execute("DELETE FROM facts WHERE content LIKE '%WINDOW_TEST%'")
    conn.commit()

    # Insert 3 synthetic events
    events = [
        ("WINDOW_TEST_1H",  now + timedelta(minutes=55)),
        ("WINDOW_TEST_15M", now + timedelta(minutes=15)),
        ("WINDOW_TEST_NOW", now + timedelta(minutes=0)),
    ]

    ids = {}
    for label, start in events:
        fid = str(uuid.uuid4())
        ids[label] = fid
        conn.execute(
            "INSERT INTO facts (id, content, date_start, date_end, importance, status, created_at) "
            "VALUES (?, ?, ?, ?, 0.8, 'active', ?)",
            (fid, label, start.isoformat(), (start + timedelta(minutes=30)).isoformat(), now.isoformat())
        )
    conn.commit()

    # Fresh watcher with empty state
    watcher = ProactiveEventsWatcher(config.workspace_dir)
    watcher.state = {"alerted_1h": [], "alerted_15m": [], "alerted_now": []}

    print("=" * 60)
    print("  3-WINDOW ALERT TEST")
    print("=" * 60)

    # --- First check: should catch all 3 windows ---
    print("\n[Round 1 — should fire ALL 3 windows]")
    alert = await watcher.check(db, config)
    if alert:
        print(f"  ALERT: {alert}")
    else:
        print("  NO ALERT (unexpected)")

    print(f"\n  State after round 1:")
    print(f"    alerted_1h:  {len(watcher.state['alerted_1h'])} event(s)")
    print(f"    alerted_15m: {len(watcher.state['alerted_15m'])} event(s)")
    print(f"    alerted_now: {len(watcher.state['alerted_now'])} event(s)")

    # --- Second check: dedup — should fire NOTHING ---
    print("\n[Round 2 — dedup check, should fire NOTHING]")
    alert2 = await watcher.check(db, config)
    if alert2 is None:
        print("  PASS: No duplicate alert fired.")
    else:
        print(f"  FAIL: Duplicate fired: {alert2}")

    # Clean up
    conn.execute("DELETE FROM facts WHERE content LIKE '%WINDOW_TEST%'")
    conn.commit()
    print("\n[Cleanup done]\n")

asyncio.run(main())
