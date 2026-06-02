# Intelligent Memory System - Run Script

# Check if virtual environment exists and activate it
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    
    # Use the virtual environment's python
    Write-Host "Starting Intelligent Memory System..." -ForegroundColor Green
    & .venv\Scripts\python.exe terminal_chat.py
} else {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run .\setup.ps1 first" -ForegroundColor Yellow
    exit 1
}
