#!/usr/bin/env python3
"""
Quick verification script to test if all dependencies are installed correctly.
Run this before pushing to GitHub to ensure the setup works.
"""

import sys

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    errors = []
    
    modules = [
        "sqlite3",
        "sqlite_vec",
        "ollama",
        "pydantic",
        "fastapi",
        "uvicorn",
        "websockets",
        "watchdog",
        "redis",
        "hiredis",
        "apscheduler",
        "yaml",
        "numpy",
        "typer",
        "httpx",
        "pytest"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except ImportError as e:
            errors.append((module, str(e)))
            print(f"  [FAIL] {module}: {e}")
    
    return errors

def test_project_imports():
    """Test project-specific imports"""
    print("\nTesting project imports...")
    errors = []
    
    project_modules = [
        "src.database.db_manager",
        "src.embeddings.embedding_manager",
        "src.search.hybrid_search",
        "src.agent.loop",
        "src.agent.tools",
        "src.memory.dreaming",
        "src.memory.facts",
    ]
    
    for module in project_modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except Exception as e:
            errors.append((module, str(e)))
            print(f"  [FAIL] {module}: {e}")
    
    return errors

def main():
    print("=" * 60)
    print("  Intelligent Memory System - Verification")
    print("=" * 60)
    print()
    
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print()
    
    import_errors = test_imports()
    project_errors = test_project_imports()
    
    print()
    print("=" * 60)
    
    if not import_errors and not project_errors:
        print("  SUCCESS - All checks passed!")
        print("=" * 60)
        print("\nYour setup is ready. You can now:")
        print("  1. Run: python terminal_chat.py")
        print("  2. Or: docker-compose up --build")
        return 0
    else:
        print("  ERROR - Some checks failed")
        print("=" * 60)
        if import_errors:
            print("\nMissing dependencies:")
            for module, error in import_errors:
                print(f"  - {module}")
            print("\nRun: pip install -r requirements.txt")
        if project_errors:
            print("\nProject import errors:")
            for module, error in project_errors:
                print(f"  - {module}: {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
