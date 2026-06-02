# Pre-Push Checklist

Before pushing to GitHub, verify everything works:

## 1. Run Verification Script

```bash
python verify_setup.py
```

All checks should pass.

## 2. Test Clean Installation

### Windows
```powershell
# Delete virtual environment
Remove-Item -Recurse -Force .venv

# Run setup
.\setup.ps1

# Test run
.\run_chat.ps1
```

### Linux/macOS
```bash
# Delete virtual environment
rm -rf .venv

# Run setup
./setup.sh

# Test run
./run_chat.sh
```

## 3. Run Tests

```bash
pytest tests/ -v
```

## 4. Check Files to Commit

Make sure you're NOT committing:
- `workspace/` directory
- `test_workspace/` directory
- `*.db` files
- `.venv/` directory
- `__pycache__/` directories
- Personal data or API keys

Check with:
```bash
git status
```

## 5. Verify Documentation

- [ ] README.md is up to date
- [ ] SETUP.md has clear instructions
- [ ] QUICKSTART.md is accurate
- [ ] All links work
- [ ] Tables are properly formatted

## 6. Final Git Commands

```bash
# Add files
git add .

# Check what will be committed
git status

# Commit
git commit -m "Your commit message"

# Push
git push origin main
```

## Common Issues to Check

- [ ] No hardcoded paths (use relative paths)
- [ ] No personal information in code
- [ ] All scripts have proper line endings (LF for .sh, CRLF for .ps1)
- [ ] requirements.txt includes all dependencies
- [ ] Docker files are up to date
- [ ] License file exists
- [ ] Contributing guide exists

## Post-Push

After pushing, test cloning from GitHub:

```bash
# Clone in a different directory
cd /tmp
git clone https://github.com/yourusername/intelligent-memory.git
cd intelligent-memory

# Test setup
./setup.sh  # or setup.ps1

# Verify it works
python verify_setup.py
```
