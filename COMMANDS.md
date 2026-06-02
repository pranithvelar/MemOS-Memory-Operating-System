# Quick Command Reference

## First Time Setup

### Windows
```powershell
.\setup.ps1
```

### Linux/macOS
```bash
chmod +x setup.sh run_chat.sh
./setup.sh
```

## Start Ollama (Required)

```bash
ollama serve
```

In another terminal, pull models (first time only):
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## Run the System

### Windows
```powershell
.\run_chat.ps1
```

### Linux/macOS
```bash
./run_chat.sh
```

## Docker Alternative

```bash
docker-compose up --build -d     # Start
docker-compose logs -f           # View logs
docker-compose down              # Stop
```

## In-Chat Commands

- `exit` or `quit` - Exit the system
- `clear` - Reset session history
- `dream` - Trigger memory consolidation
- `profile` - Show user profile
- `status` - System statistics
- `promote` - Run promotion scoring

## Verify Installation

```bash
python verify_setup.py
```

## Run Tests

```bash
pytest tests/ -v
```

## Troubleshooting

### Virtual environment not found
```bash
# Windows
.\setup.ps1

# Linux/macOS
./setup.sh
```

### Module not found errors
```bash
pip install -r requirements.txt
```

### Ollama connection refused
```bash
ollama serve
```

### Reset everything
```bash
# Windows
Remove-Item -Recurse -Force .venv
.\setup.ps1

# Linux/macOS
rm -rf .venv
./setup.sh
```

## File Locations

- Database: `workspace/memory.db`
- Dreams: `workspace/DREAMS.md`
- Promoted memories: `workspace/PROMOTED.md`
- Logs: Terminal output only

## API Endpoints

When running with Docker or FastAPI server:

- REST API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/chat`
- Docs: `http://localhost:8000/docs`
