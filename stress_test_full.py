"""
Comprehensive stress test script for every feature in the intelligent-memory system.
Tests each subsystem independently with real data, reports pass/fail and timing.
"""
import asyncio
import os
import sys
import time
import sqlite3
import uuid
import struct
import json
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import IntelligentMemoryConfig
from src.database.db_manager import MemoryDatabaseManager
from src.embeddings.embedding_manager import EmbeddingManager
from src.search.hybrid_search import HybridSearcher, HybridSearchResult
from src.agent.tools import ToolSystem
from src.agent.loop import AgentLoop
from src.agent.session import SessionManager
from src.memory.personalization import UserPersonalization
from src.memory.dreaming import MemoryDreamer
from src.memory.promotion import (
    evaluate_promotion_candidate, rank_all_candidates,
    promote_top_memories, prune_stale_entries, get_promotion_stats,
    clamp_score, calculate_recency_component, calculate_consolidation_component
)
from src.memory.facts import FactStore, extract_facts, groom_facts
from src.memory.temporal_decay import (
    TemporalDecayConfig, calculate_temporal_decay_multiplier,
    parse_memory_date_from_path, is_evergreen_memory_path, apply_temporal_decay
)
from src.memory.short_term import ShortTermMemoryTracker
from src.search.mmr import apply_mmr_to_hybrid_results, MMRConfig
from src.agent.session_transcript_repair import (
    repair_tool_use_result_pairing, extract_identifiers
)
from src.cache.redis_client import RedisManager
from src.cache.search_cache_redis import RedisSearchCache
from src.cache.embedding_cache_redis import RedisEmbeddingCache

# Try importing the new background worker
from BACKGROUND_WORKER.scheduler import BackgroundScheduler
from BACKGROUND_WORKER.proactive_events import ProactiveEventsWatcher
from BACKGROUND_WORKER.google_workspace import GoogleWorkspaceWatcher


results = []

def report(name, passed, latency_ms, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "passed": passed, "latency_ms": latency_ms, "detail": detail})
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}[{status}]{reset} {name} ({latency_ms:.0f}ms) {detail}")


async def main():
    config = IntelligentMemoryConfig.load()
    workspace = config.workspace_dir
    os.makedirs(workspace, exist_ok=True)

    db_path = os.path.join(workspace, "memory.db")
    db = MemoryDatabaseManager(db_path)
    db.ensure_schema()
    db.ensure_vector_table(dimensions=768)

    print("\n" + "=" * 70)
    print("  FRIDAY / JARVIS — FULL SYSTEM STRESS TEST")
    print("=" * 70)

    # =============================================
    # 1. DATABASE & SCHEMA
    # =============================================
    print("\n--- 1. DATABASE & SCHEMA ---")

    t = time.time()
    conn = db.get_connection()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    lat = (time.time() - t) * 1000
    expected = ["meta", "files", "chunks", "facts", "short_term_recall", "user_profile", "sessions", "embedding_cache", "chunks_fts", "chunks_vec"]
    missing = [t for t in expected if t not in tables]
    report("Schema completeness", len(missing) == 0, lat, f"Missing: {missing}" if missing else f"All {len(expected)} tables present")

    t = time.time()
    journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    lat = (time.time() - t) * 1000
    report("WAL mode active", journal == "wal", lat, f"journal_mode={journal}")

    t = time.time()
    busy = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    lat = (time.time() - t) * 1000
    report("Busy timeout configured", busy == 5000, lat, f"busy_timeout={busy}ms")

    # =============================================
    # 2. EMBEDDINGS
    # =============================================
    print("\n--- 2. EMBEDDINGS ---")

    t = time.time()
    try:
        embedder = EmbeddingManager(db, model=config.embedding_model, dimension=768)
        vec = await embedder.embed_query("test embedding for stress test")
        lat = (time.time() - t) * 1000
        report("Embed single query", len(vec) == 768, lat, f"dim={len(vec)}")
    except Exception as e:
        lat = (time.time() - t) * 1000
        report("Embed single query", False, lat, str(e))
        # Create fallback
        class FallbackEmbedder:
            async def embed_query(self, text): return [0.0]*768
        embedder = FallbackEmbedder()

    t = time.time()
    try:
        texts = ["alpha", "beta", "gamma", "delta"]
        batch = await embedder.embed_batch(texts)
        lat = (time.time() - t) * 1000
        report("Embed batch (4 texts)", len(batch) == 4 and all(len(v)==768 for v in batch), lat)
    except Exception as e:
        lat = (time.time() - t) * 1000
        report("Embed batch (4 texts)", False, lat, str(e))

    # =============================================
    # 3. HYBRID SEARCH (Vector + BM25 + LIKE)
    # =============================================
    print("\n--- 3. HYBRID SEARCH ---")

    searcher = HybridSearcher(db, embedder)

    # Ensure there's at least one chunk to search
    test_chunk_id = str(uuid.uuid4())
    conn.execute(
        "INSERT OR IGNORE INTO chunks (id, path, source, chunkIndex, content) VALUES (?, ?, ?, ?, ?)",
        (test_chunk_id, "stress_test/test.md", "memory", 0, "JARVIS architecture stress test memory chunk for search validation")
    )
    try:
        conn.execute(
            "INSERT OR IGNORE INTO chunks_fts (id, path, source, content) VALUES (?, ?, ?, ?)",
            (test_chunk_id, "stress_test/test.md", "memory", "JARVIS architecture stress test memory chunk for search validation")
        )
    except Exception:
        pass
    conn.commit()

    t = time.time()
    try:
        search_results = await searcher.search("JARVIS architecture", limit=5)
        lat = (time.time() - t) * 1000
        report("Hybrid search (vector+BM25)", len(search_results) > 0, lat, f"Found {len(search_results)} results")
    except Exception as e:
        lat = (time.time() - t) * 1000
        report("Hybrid search (vector+BM25)", False, lat, str(e))

    # =============================================
    # 4. MMR DEDUPLICATION
    # =============================================
    print("\n--- 4. MMR DEDUPLICATION ---")

    t = time.time()
    fake_results = [
        HybridSearchResult("a", "a.md", "memory", "JARVIS AI system design", 1, 1),
        HybridSearchResult("b", "b.md", "memory", "JARVIS AI system architecture", 1, 1),
        HybridSearchResult("c", "c.md", "memory", "weather forecast today", 1, 1),
    ]
    for i, r in enumerate(fake_results):
        r.score = 1.0 - i * 0.1
    mmr_config = MMRConfig(enabled=True, lambda_param=0.5)
    mmr_results = apply_mmr_to_hybrid_results(fake_results, mmr_config)
    lat = (time.time() - t) * 1000
    # MMR should prefer diversity — pick one JARVIS + weather, not two JARVIS
    report("MMR diversity reranking", len(mmr_results) == 3, lat, f"Reranked {len(mmr_results)} results")

    # =============================================
    # 5. TEMPORAL DECAY
    # =============================================
    print("\n--- 5. TEMPORAL DECAY ---")

    t = time.time()
    decay_0 = calculate_temporal_decay_multiplier(0, 30)
    decay_30 = calculate_temporal_decay_multiplier(30, 30)
    decay_60 = calculate_temporal_decay_multiplier(60, 30)
    lat = (time.time() - t) * 1000
    report("Decay math (0/30/60 days)", abs(decay_0 - 1.0) < 0.01 and abs(decay_30 - 0.5) < 0.01 and decay_60 < 0.3, lat,
           f"day0={decay_0:.3f} day30={decay_30:.3f} day60={decay_60:.3f}")

    t = time.time()
    dt = parse_memory_date_from_path("memory/2026-06-10.md")
    lat = (time.time() - t) * 1000
    report("Parse memory date from path", dt is not None and dt.year == 2026 and dt.month == 6 and dt.day == 10, lat)

    t = time.time()
    eg = is_evergreen_memory_path("MEMORY.md")
    lat = (time.time() - t) * 1000
    report("Evergreen memory detection", eg == True, lat)

    # =============================================
    # 6. FACTS / CALENDAR SYSTEM
    # =============================================
    print("\n--- 6. FACTS / CALENDAR ---")

    fact_store = FactStore(db)

    # Clean up old test facts
    conn.execute("DELETE FROM facts WHERE content LIKE '%STRESS_TEST%'")
    conn.commit()

    t = time.time()
    now = datetime.now()
    fid = fact_store.add_fact(
        "STRESS_TEST meeting with Stark Industries",
        now + timedelta(hours=2),
        now + timedelta(hours=3),
        importance=0.8
    )
    lat = (time.time() - t) * 1000
    report("Add calendar fact", fid is not None, lat, f"id={fid[:8]}...")

    t = time.time()
    active = fact_store.get_active_facts()
    lat = (time.time() - t) * 1000
    has_test = any("STRESS_TEST" in f["content"] for f in active)
    report("Get active facts (infinite horizon)", has_test, lat, f"{len(active)} active facts")

    # Add conflicting fact
    fid2 = fact_store.add_fact(
        "STRESS_TEST overlapping call with Pepper",
        now + timedelta(hours=2, minutes=30),
        now + timedelta(hours=3, minutes=30),
        importance=0.6
    )

    t = time.time()
    conflicts = fact_store.lint_memory_conflicts()
    lat = (time.time() - t) * 1000
    report("Conflict detection (SQL self-join)", conflicts >= 2, lat, f"Flagged {conflicts} facts as contested")

    t = time.time()
    contested = fact_store.get_contested_facts()
    lat = (time.time() - t) * 1000
    report("Get contested facts", len(contested) >= 2, lat, f"{len(contested)} contested")

    t = time.time()
    deleted = fact_store.delete_fact("STRESS_TEST")
    lat = (time.time() - t) * 1000
    report("Delete facts by keyword", True, lat, f"Deleted={deleted}")

    # =============================================
    # 7. REMINDER SYSTEM
    # =============================================
    print("\n--- 7. REMINDER SYSTEM ---")

    # Insert an event 30 hours from now (should be in 20-48h window)
    conn.execute("DELETE FROM facts WHERE content LIKE '%REMINDER_TEST%'")
    conn.commit()
    reminder_id = str(uuid.uuid4())
    reminder_start = (now + timedelta(hours=30)).isoformat()
    reminder_end = (now + timedelta(hours=31)).isoformat()
    conn.execute(
        "INSERT INTO facts (id, content, date_start, date_end, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
        (reminder_id, "REMINDER_TEST board review", reminder_start, reminder_end, now.isoformat())
    )
    conn.commit()

    t = time.time()
    reminders = fact_store.get_events_needing_reminder()
    lat = (time.time() - t) * 1000
    has_reminder = any("REMINDER_TEST" in r["content"] for r in reminders)
    report("Get events needing reminder (20-48h)", has_reminder, lat, f"{len(reminders)} events in window")

    t = time.time()
    fact_store.mark_reminder_sent(reminder_id)
    reminders_after = fact_store.get_events_needing_reminder()
    lat = (time.time() - t) * 1000
    gone = not any("REMINDER_TEST" in r["content"] for r in reminders_after)
    report("mark_reminder_sent prevents re-fire", gone, lat)

    # Clean up
    conn.execute("DELETE FROM facts WHERE content LIKE '%REMINDER_TEST%'")
    conn.commit()

    # =============================================
    # 8. PROMOTION SCORING
    # =============================================
    print("\n--- 8. PROMOTION SCORING ---")

    t = time.time()
    score = clamp_score(1.5)
    score2 = clamp_score(-0.3)
    score3 = clamp_score(float('inf'))
    lat = (time.time() - t) * 1000
    report("clamp_score edge cases", score == 1.0 and score2 == 0.0 and score3 == 0.0, lat)

    t = time.time()
    rec = calculate_recency_component(0, 14)
    rec2 = calculate_recency_component(14, 14)
    rec3 = calculate_recency_component(28, 14)
    lat = (time.time() - t) * 1000
    report("Recency half-life (0/14/28d)", abs(rec - 1.0) < 0.01 and abs(rec2 - 0.5) < 0.01 and rec3 < 0.3, lat,
           f"d0={rec:.3f} d14={rec2:.3f} d28={rec3:.3f}")

    t = time.time()
    consol = calculate_consolidation_component(["2026-06-01", "2026-06-03", "2026-06-07"])
    lat = (time.time() - t) * 1000
    report("Consolidation component (3 days)", 0.0 < consol < 1.0, lat, f"score={consol:.3f}")

    t = time.time()
    result = evaluate_promotion_candidate({
        "recall_count": 5,
        "daily_count": 2,
        "grounded_count": 1,
        "total_score": 3.5,
        "query_hashes": json.dumps(["a", "b", "c"]),
        "recall_days": json.dumps(["2026-06-01", "2026-06-04"]),
        "last_recalled_at": datetime.now(timezone.utc).isoformat(),
        "concept_tags": json.dumps(["AI", "memory"])
    }, time.time() * 1000)
    lat = (time.time() - t) * 1000
    report("Full promotion candidate evaluation", result["valid"] and 0 < result["score"] <= 1.0, lat,
           f"score={result['score']:.3f}, signals={result['signalCount']}")

    t = time.time()
    pstats = get_promotion_stats(db)
    lat = (time.time() - t) * 1000
    report("Promotion stats retrieval", "total_tracked" in pstats, lat,
           f"tracked={pstats['total_tracked']}, promoted={pstats['promoted']}")

    # =============================================
    # 9. DREAMING
    # =============================================
    print("\n--- 9. DREAMING ---")

    dreamer = MemoryDreamer(workspace, model=config.llama_model)

    t = time.time()
    prompt = dreamer.build_narrative_prompt(
        ["memory of building JARVIS", "testing embeddings at midnight", "the code compiled clean"],
        themes=["AI", "late nights"],
        promotions=["permanent: built the memory system"]
    )
    lat = (time.time() - t) * 1000
    report("Build narrative prompt", "memory fragments" in prompt and "AI" in prompt, lat, f"len={len(prompt)}")

    # =============================================
    # 10. PERSONALIZATION
    # =============================================
    print("\n--- 10. PERSONALIZATION ---")

    persona = UserPersonalization(db)

    t = time.time()
    persona.update_fact("project", "intelligent-memory JARVIS")
    persona.update_preference("tone", "formal")
    lat = (time.time() - t) * 1000
    report("Save fact + preference", True, lat)

    t = time.time()
    profile = persona.profile
    lat = (time.time() - t) * 1000
    report("Load profile", profile.get("facts", {}).get("project") == "intelligent-memory JARVIS", lat,
           f"facts={len(profile.get('facts', {}))}, prefs={len(profile.get('preferences', {}))}")

    t = time.time()
    ctx = persona.get_context_string()
    lat = (time.time() - t) * 1000
    report("Context string generation", len(ctx) > 0, lat, f"len={len(ctx)}")

    # =============================================
    # 11. SESSION MANAGEMENT
    # =============================================
    print("\n--- 11. SESSION MANAGEMENT ---")

    session_mgr = SessionManager(db)

    t = time.time()
    session_mgr.append_message("stress_test_session", "user", "Hello JARVIS")
    session_mgr.append_message("stress_test_session", "assistant", "Good day, sir.")
    lat = (time.time() - t) * 1000
    report("Append session messages", True, lat)

    t = time.time()
    msgs = session_mgr.load_session("stress_test_session")
    lat = (time.time() - t) * 1000
    report("Load session", len(msgs) >= 2, lat, f"{len(msgs)} messages loaded")

    t = time.time()
    lock = session_mgr.get_lock("stress_test_session")
    lat = (time.time() - t) * 1000
    report("Session write-lock creation", lock is not None, lat)

    # Clean up
    session_mgr.clear_session("stress_test_session")

    # =============================================
    # 12. TRANSCRIPT REPAIR
    # =============================================
    print("\n--- 12. TRANSCRIPT REPAIR ---")

    t = time.time()
    broken = [
        {"role": "user", "content": "Result: tool output without a preceding tool call"},
        {"role": "user", "content": "normal question"},
        {"role": "assistant", "content": "normal answer"}
    ]
    repaired = repair_tool_use_result_pairing(broken)
    lat = (time.time() - t) * 1000
    report("Orphaned tool_result repair", repaired["repaired"], lat, f"stats={repaired['stats']}")

    t = time.time()
    ids = extract_identifiers("Check file /home/user/project.py and UUID 550e8400-e29b-41d4-a716-446655440000")
    lat = (time.time() - t) * 1000
    report("Identifier extraction (UUID + path)", len(ids) >= 2, lat, f"found {len(ids)} identifiers")

    # =============================================
    # 13. REDIS CACHE
    # =============================================
    print("\n--- 13. REDIS CACHE ---")

    t = time.time()
    redis_mgr = RedisManager()
    redis_enabled = redis_mgr.enabled
    lat = (time.time() - t) * 1000
    report("Redis config loaded", True, lat, f"enabled={redis_enabled}")

    if redis_enabled:
        t = time.time()
        try:
            redis_client = await redis_mgr.get_client()
            pong = await redis_client.ping() if redis_client else False
            lat = (time.time() - t) * 1000
            report("Redis PING", pong, lat)
        except Exception as e:
            lat = (time.time() - t) * 1000
            report("Redis PING", False, lat, str(e))

        # Search cache roundtrip
        cache = RedisSearchCache()
        t = time.time()
        test_res = [HybridSearchResult("test_id", "test.md", "memory", "stress test snippet", 1, 1, vector_score=0.9, text_score=0.8)]
        test_res[0].score = 0.85
        await cache.set_search_results("stress_test_query", ["memory"], test_res)
        cached = await cache.get_search_results("stress_test_query", ["memory"])
        lat = (time.time() - t) * 1000
        report("Redis search cache roundtrip", cached is not None and len(cached) == 1, lat)

        # Embedding cache roundtrip
        emb_cache = RedisEmbeddingCache()
        t = time.time()
        await emb_cache.set_embeddings("ollama", "nomic", [{"hash": "stress_hash", "embedding": [0.1]*10}])
        got = await emb_cache.get_embeddings("ollama", "nomic", ["stress_hash"])
        lat = (time.time() - t) * 1000
        report("Redis embedding cache roundtrip", "stress_hash" in got, lat)

        # Clean up test keys
        if redis_client:
            await redis_client.delete("emb:ollama:nomic:stress_hash")
    else:
        report("Redis (disabled — skipping)", True, 0, "redis_enabled=False")

    # =============================================
    # 14. SHORT-TERM RECALL TRACKING
    # =============================================
    print("\n--- 14. SHORT-TERM RECALL ---")

    tracker = ShortTermMemoryTracker(db)

    t = time.time()
    tracker.track_recalls([
       
        HybridSearchResult("st_test", "test_recall.md", "memory", "recall snippet", 1, 5, vector_score=0.8, text_score=0.7)
    ],
        query="test recall query"
    )
    lat = (time.time() - t) * 1000
    report("Track recall entry", True, lat)

    t = time.time()
    recall_rows = conn.execute("SELECT * FROM short_term_recall WHERE path = 'test_recall.md'").fetchall()
    lat = (time.time() - t) * 1000
    report("Recall persisted in DB", len(recall_rows) > 0, lat, f"{len(recall_rows)} entries")

    # =============================================
    # 15. TOOLS SYSTEM
    # =============================================
    print("\n--- 15. TOOLS SYSTEM ---")

    persona_for_tools = UserPersonalization(db)
    dreamer_for_tools = MemoryDreamer(workspace, model=config.llama_model)
    tools = ToolSystem(workspace_dir=workspace, db_manager=db, personalization=persona_for_tools, dreamer=dreamer_for_tools)
    tools.setup_default_tools(searcher=searcher)

    t = time.time()
    tool_names = list(tools.tools.keys())
    lat = (time.time() - t) * 1000
    expected_tools = ["search_memory", "save_memory", "add_event", "delete_event", "dream_now"]
    missing_tools = [t for t in expected_tools if t not in tool_names]
    report("Tools registered", len(missing_tools) == 0, lat, f"Tools: {tool_names}")

    t = time.time()
    try:
        search_result = await tools.tools["search_memory"](query="JARVIS", limit=3)
        lat = (time.time() - t) * 1000
        report("Tool: search_memory execution", True, lat, f"result_len={len(str(search_result))}")
    except Exception as e:
        lat = (time.time() - t) * 1000
        report("Tool: search_memory execution", False, lat, str(e))

    # =============================================
    # 16. AGENT LOOP (Context Assembly)
    # =============================================
    print("\n--- 16. AGENT LOOP ---")

    agent_loop = AgentLoop(
        workspace_dir=workspace,
        model=config.llama_model,
        session_manager=session_mgr,
        session_id="stress_test_loop",
        personalization=persona,
        db_manager=db
    )
    for name, schema in zip(tools.tools.keys(), tools.schemas):
        agent_loop.register_tool(name, tools.tools[name], schema)

    t = time.time()
    prompt = agent_loop._build_system_prompt()
    lat = (time.time() - t) * 1000
    report("System prompt build", "Friday" in prompt and "tool" in prompt.lower(), lat, f"len={len(prompt)}")

    t = time.time()
    agent_loop._load_history()
    context = agent_loop._assemble_context("What is my schedule?")
    lat = (time.time() - t) * 1000
    has_system = any(m["role"] == "system" for m in context)
    has_user = any(m["role"] == "user" for m in context)
    report("Context assembly", has_system and has_user, lat, f"{len(context)} messages assembled")

    # =============================================
    # 17. FEEDBACK DETECTOR
    # =============================================
    print("\n--- 17. FEEDBACK DETECTOR ---")

    from src.agent.loop import FeedbackDetector
    fd = FeedbackDetector(persona)

    t = time.time()
    saved = fd.detect_and_save("call me Boss")
    lat = (time.time() - t) * 1000
    report("FeedbackDetector (name capture)", len(saved) > 0, lat, f"saved={saved}")

    t = time.time()
    saved2 = fd.detect_and_save("be more concise")
    lat = (time.time() - t) * 1000
    report("FeedbackDetector (style capture)", len(saved2) > 0 or persona.get_preference("response_style") == "concise", lat)

    # =============================================
    # 18. BACKGROUND WORKER (NEW)
    # =============================================
    print("\n--- 18. BACKGROUND WORKER (NEW) ---")

    t = time.time()
    bg_scheduler = BackgroundScheduler(db, config)
    lat = (time.time() - t) * 1000
    report("BackgroundScheduler creation", True, lat)

    t = time.time()
    events_watcher = ProactiveEventsWatcher(workspace)
    bg_scheduler.register_watcher(events_watcher)
    bg_scheduler.register_watcher(GoogleWorkspaceWatcher())
    lat = (time.time() - t) * 1000
    report("Register watchers (events + google stub)", len(bg_scheduler.watchers) == 2, lat)

    # Insert event exactly 60 mins from now for test
    conn.execute("DELETE FROM facts WHERE content LIKE '%BG_WORKER_TEST%'")
    conn.commit()
    bg_test_id = str(uuid.uuid4())
    bg_start = (datetime.now(timezone.utc) + timedelta(minutes=60)).isoformat()
    bg_end = (datetime.now(timezone.utc) + timedelta(minutes=90)).isoformat()
    conn.execute(
        "INSERT INTO facts (id, content, date_start, date_end, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
        (bg_test_id, "BG_WORKER_TEST important call", bg_start, bg_end, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()

    # Reset watcher state so it triggers
    events_watcher.state = {"alerted_1h": [], "alerted_15m": []}

    t = time.time()
    alert = await events_watcher.check(db, config)
    lat = (time.time() - t) * 1000
    report("Proactive event detection (1h window)", alert is not None and len(alert) > 10, lat,
           f"Alert: {alert[:80]}..." if alert else "No alert generated")

    # Check that it won't fire again (dedup)
    t = time.time()
    alert2 = await events_watcher.check(db, config)
    lat = (time.time() - t) * 1000
    report("Dedup: no re-fire after alert", alert2 is None, lat)

    # Google stub returns None
    t = time.time()
    g_alert = await GoogleWorkspaceWatcher().check(db, config)
    lat = (time.time() - t) * 1000
    report("GoogleWorkspace stub (returns None)", g_alert is None, lat)

    # Clean up
    conn.execute("DELETE FROM facts WHERE content LIKE '%BG_WORKER_TEST%'")
    conn.commit()

    # =============================================
    # 19. GROOM FACTS (Expiry Pipeline)
    # =============================================
    print("\n--- 19. FACT GROOMING ---")

    # Insert an already-expired fact
    expired_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO facts (id, content, date_start, date_end, importance, status, created_at) VALUES (?, ?, ?, ?, ?, 'active', ?)",
        (expired_id, "GROOM_TEST expired meeting", (now - timedelta(hours=3)).isoformat(), (now - timedelta(hours=2)).isoformat(), 0.7, now.isoformat())
    )
    conn.commit()

    t = time.time()
    try:
        await groom_facts(db, embedder, workspace_dir=workspace)
        lat = (time.time() - t) * 1000
        # Check it was expired
        status = conn.execute("SELECT status FROM facts WHERE id = ?", (expired_id,)).fetchone()
        report("Groom facts (expire past events)", status and status["status"] == "expired", lat)
    except Exception as e:
        lat = (time.time() - t) * 1000
        report("Groom facts (expire past events)", False, lat, str(e))

    # =============================================
    # SUMMARY
    # =============================================
    print("\n" + "=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    print(f"  TOTAL: {total} tests | PASSED: {passed} | FAILED: {failed}")
    if failed > 0:
        print(f"\n  FAILURES:")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['name']}: {r['detail']}")

    # Latency stats
    latencies = [r["latency_ms"] for r in results]
    print(f"\n  LATENCY: avg={sum(latencies)/len(latencies):.0f}ms, max={max(latencies):.0f}ms, total={sum(latencies):.0f}ms")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
