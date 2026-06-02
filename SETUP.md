# Setup Guide - Intelligent Memory System

This guide will help you set up the Intelligent Memory System on any machine or IDE.

## Prerequisites

1. **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
2. **Ollama** - [Install Ollama](https://ollama.ai/)
3. **Git** (optional) - For cloning the repository

## Quick Start

### Windows

```powershell
# 1. Run setup (first time only)
.\setup.ps1

# 2. Start the system
.\run_chat.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Linux/macOS

```bash
# 1. Make scripts executable
chmod +x setup.sh run_chat.sh

# 2. Run setup (first time only)
./setup.sh

# 3. Start the system
./run_chat.sh
```

## Manual Setup

If the automated scripts don't work:

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the system
python terminal_chat.py
```

## Docker Setup

If you prefer Docker:

```bash
# 1. Build and start
docker-compose up --build -d

# 2. Access the API
# REST: http://localhost:8000
# WebSocket: ws://localhost:8000/ws/chat

# 3. Stop
docker-compose down
```

## Verify Installation

After setup, check that everything works:

```bash
# 1. Activate virtual environment
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

# 2. Check Python packages
pip list | grep -E "ollama|fastapi|sqlite-vec"

# 3. Start Ollama (in separate terminal)
ollama serve

# 4. Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 5. Run the system
python terminal_chat.py
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'sqlite_vec'"

**Solution:** Activate virtual environment and reinstall:
```bash
# Windows
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

### "Ollama connection refused"

**Solution:** Start Ollama first:
```bash
ollama serve
```

### Virtual environment not activating on Windows

**Solution:** Set execution policy:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Import errors when running tests

**Solution:** Install dev dependencies:
```bash
pip install pytest
```

## IDE-Specific Setup

### VS Code

1. Open the project folder
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
3. Type "Python: Select Interpreter"
4. Choose `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/macOS)
5. Run `.\setup.ps1` in terminal

### PyCharm

1. Open the project folder
2. Go to File → Settings → Project → Python Interpreter
3. Click gear icon → Add → Existing Environment
4. Select `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/macOS)
5. Run `.\setup.ps1` in terminal

### Cursor/Other IDEs

1. Open project folder
2. Run setup script in integrated terminal
3. Configure Python interpreter to use `.venv`

## Project Structure

```
intelligent-memory/
├── src/                  # Source code
│   ├── agent/           # Agent loop & tools
│   ├── api/             # FastAPI server
│   ├── database/        # SQLite management
│   ├── embeddings/      # Embedding generation
│   ├── memory/          # Memory systems
│   └── search/          # Hybrid search
├── workspace/           # Runtime data & memory DB
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
├── setup.ps1           # Windows setup
├── setup.sh            # Unix setup
├── run_chat.ps1        # Windows runner
├── run_chat.sh         # Unix runner
└── terminal_chat.py    # Main entry point
```

## Next Steps

After setup:

1. **Start Ollama:** `ollama serve`
2. **Run chat:** `.\run_chat.ps1` or `./run_chat.sh`
3. **Try commands:**
   - `exit` - Exit the system
   - `clear` - Reset session
   - `dream` - Trigger memory consolidation
   - `profile` - Show user profile
   - `status` - System statistics

## Support

If you encounter issues:

1. Check that Python 3.11+ is installed: `python --version`
2. Verify Ollama is running: `curl http://localhost:11434`
3. Check virtual environment is activated (prompt shows `(intelligent-memory)`)
4. Review error messages carefully
5. Try manual setup steps above
