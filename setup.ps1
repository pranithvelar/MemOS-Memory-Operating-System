# Intelligent Memory System - Complete Setup Script

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Intelligent Memory System - Complete Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "  ✗ Python not found. Please install Python 3.11+ first." -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Ollama
Write-Host "[2/7] Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaCheck = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Ollama installed" -ForegroundColor Green
    } else {
        throw "Ollama not found"
    }
} catch {
    Write-Host "  ⚠ Ollama not found. Please install from: https://ollama.ai/" -ForegroundColor Yellow
    Write-Host "  The system will continue but won't work without Ollama." -ForegroundColor Yellow
}

# Remove broken virtual environment if it exists
Write-Host "[3/7] Cleaning up..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
    Write-Host "  ✓ Cleaned up" -ForegroundColor Green
} else {
    Write-Host "  ✓ No cleanup needed" -ForegroundColor Green
}

# Create virtual environment
Write-Host "[4/7] Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "[5/7] Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to activate. Run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "[6/7] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ pip upgraded" -ForegroundColor Green
} else {
    Write-Host "  ⚠ pip upgrade failed, continuing..." -ForegroundColor Yellow
}

# Install dependencies
Write-Host "[7/7] Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ All dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Installation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Start Ollama (if not running):" -ForegroundColor White
Write-Host "     ollama serve" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Pull required models (first time only):" -ForegroundColor White
Write-Host "     ollama pull llama3.1:8b" -ForegroundColor Gray
Write-Host "     ollama pull nomic-embed-text" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run the chat interface:" -ForegroundColor White
Write-Host "     .\run_chat.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Or use Docker:" -ForegroundColor White
Write-Host "     docker-compose up --build" -ForegroundColor Gray
Write-Host ""
Write-Host "For troubleshooting, see SETUP.md" -ForegroundColor Yellow
Write-Host ""
