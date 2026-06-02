# Quick Start Guide

## First Time Setup

Run this ONCE when you first clone/open the project:

### Windows
```powershell
.\setup.ps1
```

### Linux/macOS
```bash
chmod +x setup.sh run_chat.sh
./setup.sh
```

## Running the System

### Windows
```powershell
.\run_chat.ps1
```

### Linux/macOS
```bash
./run_chat.sh
```

## Prerequisites

Make sure Ollama is running before starting the chat:

```bash
ollama serve
```

Pull required models (first time only):
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## Troubleshooting

### "ModuleNotFoundError"
Your Python environment isn't using the virtual environment. Solution:

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python terminal_chat.py
```

**Linux/macOS:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python terminal_chat.py
```

### "ExecutionPolicy" error on Windows
Run this first:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Virtual environment not found
Create it manually:
```bash
python -m venv .venv
```

Then run setup again.

## Commands in Chat

- `exit` or `quit` - Exit the system
- `clear` - Reset session history
- `dream` - Trigger memory consolidation
- `profile` - Show user profile
- `status` - System statistics
- `promote` - Run promotion scoring

## Files Created

The system will automatically create:
- `workspace/memory.db` - Main SQLite database with all data
- `workspace/DREAMS.md` - Consolidated memories
- `workspace/PROMOTED.md` - Important promoted memories

All state is stored in SQLite - no JSON files needed!
