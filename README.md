# Intelligent Memory System

> ⚠️ **Project Status:** ~75% complete. Core architecture is production-ready with JARVIS-level proactive intelligence. Daily improvements ongoing.

A local-first AI memory system that learns, adapts, and proactively assists you. Built with Python, SQLite, and Ollama—inspired by OpenClaw's architecture with unique innovations in temporal reasoning and autonomous learning.

## What Makes This Different

Unlike static RAG systems that just retrieve text, this system:
- **Remembers intelligently** - Understands context, importance, and relationships
- **Forgets strategically** - Auto-prunes stale information
- **Learns from you** - Adapts tone, style, and behavior through natural interaction
- **Proactively helps** - Detects conflicts, sends reminders, surfaces relevant memories
- **Runs 100% locally** - Complete privacy, no cloud dependencies

## Core Features

### 🧠 Intelligent Memory
- **Hybrid Search**: FTS5 BM25 + Vector KNN + MMR diversity re-ranking
- **Temporal Decay**: 30-day half-life scoring with evergreen exemptions
- **3-Stage Compaction**: Progressive fallback (full → partial → hard) prevents crashes
- **Self-Healing Transcripts**: Auto-repairs orphaned tool calls/results on load

### 📅 JARVIS-Style Calendar
- **Infinite-Horizon Awareness**: Sees ALL future events with countdown labels
- **Proactive 3-Window Alerts**: 1 hour, 15 minutes, and NOW (exact start time)
- **Conflict Detection**: SQL self-join linter catches overlapping events
- **Smart Reminders**: 24-48 hour advance warnings with deduplication

### 🎯 Adaptive Intelligence
- **6D Promotion Scoring**: Frequency, relevance, diversity, recency, consolidation, conceptual
- **Background Reflection**: Autonomous learning every 12 messages
- **Dreaming Pipeline**: LLM consolidates short-term memories into durable knowledge
- **Personalization Agents**: Self-realization + feedback detection

### 🛡️ Production-Ready
- **Session Write-Locks**: Prevents concurrent corruption
- **Transcript Repair**: Fixes malformed JSON, orphaned tool calls
- **Type Coercion**: Safeguards against parameter errors
- **Redis + SQLite Cache**: Dual-layer with automatic fallback

### 🚀 Background Worker System
- **Async Scheduler**: Runs continuously, 1-minute resolution
- **3-Tiered Alerts**: 45-65 min, 10-20 min, ±2 min windows per event
- **JARVIS Voice**: Formal "Sir, [event] is starting now" style
- **Google Workspace Stub**: Ready for OAuth2/MCP/n8n integration

## Quick Setup

### Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Ollama** - [Install](https://ollama.ai/)

### Installation

#### Windows
```powershell
.\setup.ps1      # First time only - installs everything
.\run_chat.ps1   # Start the system
```

#### Linux/macOS
```bash
chmod +x setup.sh run_chat.sh
./setup.sh       # First time only
./run_chat.sh    # Start the system
```

#### Docker
```bash
docker-compose up --build -d
# Access API: http://localhost:8000
```

**See [SETUP.md](SETUP.md) for detailed instructions.**

## Project Structure

```
intelligent-memory/
├── src/
│   ├── agent/          # ReAct loop, tools, session management
│   ├── memory/         # Dreaming, promotion, facts, personalization
│   ├── search/         # Hybrid search, MMR re-ranking
│   ├── database/       # SQLite + sqlite-vec management
│   └── embeddings/     # Embedding generation with caching
├── BACKGROUND_WORKER/  # Proactive alerts, Google stub
├── tests/              # Comprehensive test suite (60+ tests)
└── terminal_chat.py    # Main entry point
```

## Technical Highlights

### Memory Architecture
- **Storage**: SQLite WAL + sqlite-vec for vectors
- **Search**: BM25 (keyword) + KNN (semantic) + MMR (diversity)
- **Caching**: Redis primary, SQLite fallback
- **Session**: SQL table with auto-repair on load

### Intelligence Pipeline
```
User Input → Memory Search (proactive) → Agent Loop (ReAct)
  ↓
Facts Extraction → Conflict Detection → Reminder Check
  ↓
LLM Response → Background Compaction → Dreaming (every 5 writes)
  ↓
Promotion Scoring (6D) → PROMOTED.md
```

### Calendar System
```
Event Added → Infinite Itinerary (no day cap)
  ↓
Background Worker (1-min checks)
  ↓
3 Alert Windows: 1h, 15m, NOW
  ↓
LLM Generates JARVIS-style Alert → Deduplication → Display
```

## Unique Innovations

| Feature | Description | Status |
|---------|-------------|--------|
| **Temporal Conflict Detection** | SQL self-join for overlapping events | ✅ |
| **Infinite-Horizon Calendar** | No 7-day cap, full future visibility | ✅ |
| **3-Window Proactive Alerts** | 1h, 15m, NOW alerts with deduplication | ✅ |
| **Background Compaction** | Zero-latency summarization (post-response) | ✅ |
| **Self-Healing Transcripts** | Auto-repair on load with persistence | ✅ |
| **Identifier Preservation** | UUIDs, hashes, paths intact through compaction | ✅ |
| **6D Promotion Scoring** | Custom heuristic algorithm | ✅ |
| **Background Reflection** | Autonomous learning every 12 messages | ✅ |

## Comparison to OpenClaw

This project is a **conceptual port** of OpenClaw's memory architecture to Python with unique additions.

### Similarity Analysis

| Dimension | Similarity % |
|-----------|-------------|
| Concepts & Architecture | ~70% |
| Actual Code / Logic | ~15% |
| File Structure | ~25% |
| **Overall** | **~25%** |

### What This Project Adds

- ✅ Infinite-horizon calendar with conflict detection
- ✅ 3-window proactive alert system (JARVIS-style)
- ✅ Background compaction (zero latency impact)
- ✅ Self-healing transcripts with auto-repair
- ✅ Temporal reasoning focused on scheduling

### What OpenClaw Has

- Multi-channel support (WhatsApp, Telegram, 20+ platforms)
- Voice integration (macOS/iOS/Android)
- Plugin SDK & marketplace
- Multi-agent routing system
- 3-phase dreaming (Light → REM → Deep)

**See [OPENCLAW_COMPARISON.md](OPENCLAW_COMPARISON.md) for detailed technical analysis.**

## Testing

Comprehensive test suite covering all subsystems:

```bash
# Full stress test (63+ tests)
python stress_test_full.py

# Individual test suites
pytest tests/
```

## Attribution

~70% of **concepts and architecture** inspired by [OpenClaw](https://github.com/openclaw/openclaw). ~15% actual code similarity (SQLite/vector plumbing). Rest is original Python implementation with innovations in temporal reasoning, proactive intelligence, and autonomous learning.

## Roadmap

- [x] Core memory (SQLite + vector search)
- [x] Hybrid search + MMR
- [x] Dreaming pipeline
- [x] 6D promotion scoring
- [x] Temporal conflict detection
- [x] Proactive alert system
- [x] Background compaction
- [x] Self-healing transcripts
- [ ] Web UI interface
- [ ] Voice integration (TTS/STT)
- [ ] Google Workspace integration
- [ ] Multi-language support
- [ ] Plugin system

## License

MIT License - See [LICENSE](LICENSE) for details.

## Links

- [Setup Guide](SETUP.md)
- [Quick Commands](COMMANDS.md)
- [OpenClaw Comparison](OPENCLAW_COMPARISON.md)
- [Contributing](CONTRIBUTING.md)
