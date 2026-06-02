#!/bin/bash

# Intelligent Memory System - Complete Setup Script

echo "=================================================="
echo "  Intelligent Memory System - Complete Setup"
echo "=================================================="
echo ""

# Check Python
echo "[1/7] Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✓ $PYTHON_VERSION"
else
    echo "  ✗ Python3 not found. Please install Python 3.11+ first."
    echo "  Download from: https://www.python.org/downloads/"
    exit 1
fi

# Check Ollama
echo "[2/7] Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✓ Ollama installed"
else
    echo "  ⚠ Ollama not found. Please install from: https://ollama.ai/"
    echo "  The system will continue but won't work without Ollama."
fi

# Clean up
echo "[3/7] Cleaning up..."
if [ -d ".venv" ]; then
    echo "  Removing old virtual environment..."
    rm -rf .venv
    echo "  ✓ Cleaned up"
else
    echo "  ✓ No cleanup needed"
fi

# Create virtual environment
echo "[4/7] Creating virtual environment..."
python3 -m venv .venv
if [ $? -eq 0 ]; then
    echo "  ✓ Virtual environment created"
else
    echo "  ✗ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "[5/7] Activating virtual environment..."
source .venv/bin/activate
echo "  ✓ Virtual environment activated"

# Upgrade pip
echo "[6/7] Upgrading pip..."
python -m pip install --upgrade pip --quiet
if [ $? -eq 0 ]; then
    echo "  ✓ pip upgraded"
else
    echo "  ⚠ pip upgrade failed, continuing..."
fi

# Install dependencies
echo "[7/7] Installing dependencies..."
echo "  This may take a few minutes..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "  ✓ All dependencies installed"
else
    echo "  ✗ Installation failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Start Ollama (if not running):"
echo "     ollama serve"
echo ""
echo "  2. Pull required models (first time only):"
echo "     ollama pull llama3.1:8b"
echo "     ollama pull nomic-embed-text"
echo ""
echo "  3. Run the chat interface:"
echo "     ./run_chat.sh"
echo ""
echo "  4. Or use Docker:"
echo "     docker-compose up --build"
echo ""
echo "For troubleshooting, see SETUP.md"
echo ""
