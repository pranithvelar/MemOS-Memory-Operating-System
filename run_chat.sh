#!/bin/bash

# Intelligent Memory System - Run Script

# Check if virtual environment exists and activate it
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    
    # Run the chat
    echo "Starting Intelligent Memory System..."
    python terminal_chat.py
else
    echo "Error: Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi
