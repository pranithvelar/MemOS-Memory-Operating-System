r"""
One-time migration: Import existing JSON flat-file data into the new SQLite tables.

Usage:
    cd "c:\Users\prani\OneDrive\Desktop\EXPERIMENTS\ADV memory architecture\intelligent-memory"
    python migrate_json_to_db.py

Safe to run multiple times — uses INSERT OR IGNORE to avoid duplicates.
"""
import os
import sys
import json
import glob

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import IntelligentMemoryConfig
from src.database.db_manager import MemoryDatabaseManager


def migrate_facts(conn, workspace: str):
    """Import facts.json → facts table."""
    facts_path = os.path.join(workspace, "memory", "facts.json")
    if not os.path.exists(facts_path):
        print("  [SKIP] No facts.json found")
        return 0
    
    with open(facts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for fid, fact in data.get("facts", {}).items():
        try:
            conn.execute(
                "INSERT OR IGNORE INTO facts (id, content, date_start, date_end, importance, confidence, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    fid,
                    fact.get("content", ""),
                    fact.get("date_start", ""),
                    fact.get("date_end", ""),
                    fact.get("importance", 0.5),
                    fact.get("confidence", 1.0),
                    fact.get("status", "active"),
                    fact.get("created_at", "")
                )
            )
            count += 1
        except Exception as e:
            print(f"  [WARN] Failed to migrate fact {fid}: {e}")
    
    conn.commit()
    print(f"  [OK] Migrated {count} facts from facts.json")
    return count


def migrate_short_term_recall(conn, workspace: str):
    """Import short-term-recall.json and short_term_recall.json → short_term_recall table."""
    count = 0
    for filename in ["short-term-recall.json", "short_term_recall.json"]:
        store_path = os.path.join(workspace, "memory", ".dreams", filename)
        if not os.path.exists(store_path):
            continue
        
        with open(store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key, entry in data.get("entries", {}).items():
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO short_term_recall 
                    (key, path, start_line, end_line, source, snippet, recall_count, daily_count,
                     grounded_count, total_score, max_score, first_recalled_at, last_recalled_at,
                     query_hashes, recall_days, concept_tags, claim_hash, promoted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entry.get("key", key),
                        entry.get("path", ""),
                        entry.get("startLine", entry.get("start_line", 0)),
                        entry.get("endLine", entry.get("end_line", 0)),
                        entry.get("source", "memory"),
                        entry.get("snippet", ""),
                        entry.get("recallCount", entry.get("recall_count", 0)),
                        entry.get("dailyCount", entry.get("daily_count", 0)),
                        entry.get("groundedCount", entry.get("grounded_count", 0)),
                        entry.get("totalScore", entry.get("total_score", 0)),
                        entry.get("maxScore", entry.get("max_score", 0)),
                        entry.get("firstRecalledAt", entry.get("first_recalled_at", "")),
                        entry.get("lastRecalledAt", entry.get("last_recalled_at", "")),
                        json.dumps(entry.get("queryHashes", entry.get("query_hashes", []))),
                        json.dumps(entry.get("recallDays", entry.get("recall_days", []))),
                        json.dumps(entry.get("conceptTags", entry.get("concept_tags", []))),
                        entry.get("claimHash", entry.get("claim_hash", "")),
                        entry.get("promotedAt", entry.get("promoted_at", None))
                    )
                )
                count += 1
            except Exception as e:
                print(f"  [WARN] Failed to migrate recall entry {key}: {e}")
        
        print(f"  [OK] Migrated from {filename}")
    
    conn.commit()
    if count == 0:
        print("  [SKIP] No short-term recall files found")
    else:
        print(f"  [OK] Migrated {count} recall entries total")
    return count


def migrate_user_profile(conn, workspace: str):
    """Import user_profile.json → user_profile table."""
    profile_path = os.path.join(workspace, "memory", ".dreams", "user_profile.json")
    if not os.path.exists(profile_path):
        print("  [SKIP] No user_profile.json found")
        return 0
    
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for key, value in data.get("facts", {}).items():
        conn.execute(
            "INSERT OR IGNORE INTO user_profile (key, category, value) VALUES (?, 'fact', ?)",
            (key, str(value))
        )
        count += 1
    
    for key, value in data.get("preferences", {}).items():
        conn.execute(
            "INSERT OR IGNORE INTO user_profile (key, category, value) VALUES (?, 'preference', ?)",
            (key, str(value))
        )
        count += 1
    
    conn.commit()
    print(f"  [OK] Migrated {count} profile entries from user_profile.json")
    return count


def migrate_sessions(conn, workspace: str):
    """Import *.jsonl session files → sessions table."""
    sessions_dir = os.path.join(workspace, "memory", "sessions")
    if not os.path.isdir(sessions_dir):
        print("  [SKIP] No sessions directory found")
        return 0
    
    count = 0
    for jsonl_file in glob.glob(os.path.join(sessions_dir, "*.jsonl")):
        session_id = os.path.splitext(os.path.basename(jsonl_file))[0]
        
        # Check if already migrated
        existing = conn.execute(
            "SELECT COUNT(*) as c FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if existing and existing["c"] > 0:
            continue
        
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    msg = json.loads(line)
                    tc = json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else None
                    conn.execute(
                        "INSERT INTO sessions (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
                        (session_id, msg.get("role", "user"), msg.get("content", ""), tc)
                    )
                    count += 1
        except Exception as e:
            print(f"  [WARN] Failed to migrate session {session_id}: {e}")
    
    conn.commit()
    print(f"  [OK] Migrated {count} session messages")
    return count


def migrate_content_hashes(conn, workspace: str):
    """Import .content_hashes.json → meta table."""
    hash_path = os.path.join(workspace, "memory", ".content_hashes.json")
    if not os.path.exists(hash_path):
        print("  [SKIP] No .content_hashes.json found")
        return 0
    
    with open(hash_path, "r", encoding="utf-8") as f:
        hashes = json.load(f)
    
    count = 0
    for h, filename in hashes.items():
        conn.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
            (f"content_hash:{h}", filename)
        )
        count += 1
    
    conn.commit()
    print(f"  [OK] Migrated {count} content hashes")
    return count


def main():
    config = IntelligentMemoryConfig.load()
    workspace = config.workspace_dir
    
    db_path = os.path.join(workspace, "memory.db")
    print(f"Migration target: {db_path}")
    print(f"Workspace: {workspace}")
    print()
    
    db_manager = MemoryDatabaseManager(db_path)
    db_manager.ensure_schema()
    conn = db_manager.get_connection()
    
    print("1. Migrating facts...")
    migrate_facts(conn, workspace)
    
    print("2. Migrating short-term recall...")
    migrate_short_term_recall(conn, workspace)
    
    print("3. Migrating user profile...")
    migrate_user_profile(conn, workspace)
    
    print("4. Migrating sessions...")
    migrate_sessions(conn, workspace)
    
    print("5. Migrating content hashes...")
    migrate_content_hashes(conn, workspace)
    
    print("\n[SUCCESS] Migration complete!")
    
    # Print summary
    facts_count = conn.execute("SELECT COUNT(*) as c FROM facts").fetchone()["c"]
    recall_count = conn.execute("SELECT COUNT(*) as c FROM short_term_recall").fetchone()["c"]
    profile_count = conn.execute("SELECT COUNT(*) as c FROM user_profile").fetchone()["c"]
    session_count = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    
    print(f"\n  Facts:          {facts_count}")
    print(f"  Recall entries: {recall_count}")
    print(f"  Profile items:  {profile_count}")
    print(f"  Session msgs:   {session_count}")
    
    db_manager.close()


if __name__ == "__main__":
    main()
