# Intelligent Memory System

> ⚠️ **Project Status:** This project is currently ~70% complete and under active development. The core architecture is solid, but some features are still being refined. Expect improvements daily.

An open-source, local-first intelligent memory architecture ported from the TypeScript OpenClaw stack to a production-ready Python framework. Designed to give AI agents persistent, dynamic, and evolving memory layers.

## Features

**Phase 1: Core Memory**
- Local SQLite Database scaled with `sqlite-vec`.
- Hybrid Search combining FTS5 BM25 + Vector KNN.
- MMR (Maximal Marginal Relevance) Diversity Re-ranking.
- Temporal Recency Scaling.

**Phase 2: Intelligence Layer**
- **Dreaming Subsystem**: Llama 3.1:8b processes daily "short-term logs" and summarizes them into durable `MEMORY.md` chunks during a semantic consolidation pass.
- **Promotion Scoring**: 6-dimensional heuristics (frequency, relevance, diversity, recency, consolidation, conceptual) grading memory importance dynamically.
- **Agent Reasoning**: ReAct style thought-action loop interacting locally with the memory tools.

**Phase 3: Production**
- Standardized FastAPI endpoint covering REST + WebSockets.
- Docker & Docker Compose setup connecting immediately to `ollama`.
- Async Concurrency batcher to prevent local model overload.
- Wiki document ingestion pipelines allowing manual memory side-loading.

## Quick Setup

### Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Ollama** - [Install](https://ollama.ai/)
3. **Git** (optional)

### Installation

#### Windows
```powershell
.\setup.ps1      # First time only - installs everything
.\run_chat.ps1   # Start the system
```

#### Linux/macOS
```bash
chmod +x setup.sh run_chat.sh
./setup.sh       # First time only - installs everything
./run_chat.sh    # Start the system
```

#### Docker
```bash
docker-compose up --build -d
# Access API: http://localhost:8000
```

**See [SETUP.md](SETUP.md) for detailed instructions and troubleshooting.**

### Example Integration
To talk to the memory system via python:
```python
import json
import websockets
import asyncio

async def chat():
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        await ws.send(json.dumps({"message": "Hello, please remember that my favorite color is Blue.", "session_id": "test_1"}))
        res = json.loads(await ws.recv())
        print(res)
```

## Structure
- `src/indexing/`: Watchers, Chunkers, and Document splitters.
- `src/memory/`: SQLite management, Embeddings, Temporal Decay, Dreaming algorithms.
- `src/search/`: Hybrid search logic and MMR algorithm execution.
- `src/agent/`: Reasoning loop, Tools configuration, and Session continuity state.
- `src/config/` & `src/utils/`: Globals, settings, and asynchronous batchers.
- `src/api/`: ReAct / WebSocket exposure.

## Technical Comparison: OpenClaw vs This Project

This project is a **conceptual port** of OpenClaw's memory subsystem to Python, with unique innovations added. Here's the breakdown:

### Code Similarity Analysis

| Dimension | Similarity % |
|-----------|-------------|
| Concepts & Architecture | ~70% |
| Actual Code / Logic | ~15% |
| File Structure | ~25% |
| **Overall (weighted)** | **~20-25%** |

### What is OpenClaw?

OpenClaw is a **massive production TypeScript monorepo** — a full personal AI assistant platform with:
- Multi-channel inbox (WhatsApp, Telegram, Slack, Discord, iMessage, 20+ more)
- Companion apps (macOS, iOS, Android)
- Voice Wake / Talk Mode
- Live Canvas (visual workspace)
- Plugin SDK & Skills registry
- Always-on gateway daemon
- Multi-agent routing

This project is a **terminal chatbot** with local SQLite memory backend focused on the memory architecture.

### Feature Comparison

| Feature | This Project | OpenClaw |
|---------|-------------|----------|
| **Language** | Python | TypeScript |
| **LLM Backend** | Ollama (local) | Any provider (OpenAI, Claude) |
| **Memory Storage** | SQLite WAL | SQLite + remote backends |
| **Vector Search** | `sqlite-vec` | `sqlite-vec` (same library) |
| **Full Text Search** | FTS5 + Porter | FTS5 + unicode61/trigram |
| **Hybrid Search** | BM25 + Vector + MMR | BM25 + Vector KNN |
| **Dreaming** | LLM consolidation | Multi-phase narrative |
| **Session Storage** | SQL table | JSONL files |
| **Deployment** | Docker Compose | Multiple platforms |
| **Channels** | Terminal only | 20+ messaging platforms |
| **Voice** | None | macOS/iOS/Android |
| **Multi-agent** | Single agent | Full routing system |
| **Multilingual** | English only | 7 languages |

### Unique Innovations in This Project

| Feature | Status |
|---------|--------|
| **Calendar/Facts Extraction** | ✅ LLM-driven temporal facts system |
| **Temporal Conflict Detection** | ✅ SQL self-join linter for scheduling conflicts |
| **6-Dimensional Promotion Scoring** | ✅ Custom heuristic algorithm |
| **Short-term Recall Tracking** | ✅ Explicit SQL tracking table |
| **Background Reflection Agent** | ✅ Autonomous learning every 12 messages |
| **JSON → DB Migration** | ✅ Migration tooling included |
| **100% Local Operation** | ✅ No cloud APIs required |
| **Simple Setup** | ✅ Single command installation |

### What OpenClaw Has That This Doesn't

- 20+ messaging channels (WhatsApp, Telegram, Slack, etc.)
- Voice wake & Talk mode
- Mobile/desktop companion apps
- Plugin SDK & marketplace
- Multi-agent routing system
- Sandboxed session execution
- Full multilingual support (7 languages)
- OAuth & security features
- Always-on daemon mode
- Live Canvas interface

## Attribution

~70% of the **concepts and architecture** are inspired by [OpenClaw](https://github.com/openclaw/openclaw), with ~15% actual code similarity (mainly SQLite/sqlite-vec plumbing). The rest is original Python implementation with unique features like temporal conflict detection, 6-dimensional promotion scoring, and background reflection agents.

## Roadmap

- [ ] Complete test coverage (currently ~60%)
- [ ] Multi-language support
- [ ] Web UI interface
- [ ] Mobile API endpoints
- [ ] Plugin system
- [ ] Voice integration
- [ ] Advanced conflict resolution
- [ ] Performance optimizations

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

This project is under active development. Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
