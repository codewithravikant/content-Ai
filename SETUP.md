# Setup Guide - macOS

## Quick Fix for Python/Pip Commands

On macOS, Python 3 is typically available as `python3` (not `python`). Here's how to set up:

### Option 1: Use python3/pip3 directly (Recommended)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Option 2: Create aliases (Add to ~/.zshrc)

```bash
# Add these lines to ~/.zshrc
alias python=python3
alias pip=pip3

# Then reload your shell
source ~/.zshrc
```

### Option 3: Use Docker (Easiest - No Python setup needed!)

```bash
# Just run this from the project root
docker-compose up --build
```

## Step-by-Step Manual Setup

1. **Navigate to backend directory**
   ```bash
   cd /Users/ravikantpandit/koodsisu/ghostwriter/backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   ```

3. **Activate virtual environment** (IMPORTANT: Do this BEFORE installing packages!)
   ```bash
   source venv/bin/activate
   ```
   You should see `(venv)` appear at the start of your prompt.

4. **Install dependencies** (use `pip` or `python3 -m pip` after activation)
   ```bash
   pip install -r requirements.txt
   # Or: python3 -m pip install -r requirements.txt
   ```
   ⚠️ **Note:** After activating venv, use `pip` (not `pip3`) - the venv's pip will be used automatically.

5. **Set environment variable**
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

6. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Verify Python Installation

Check if Python 3 is installed:
```bash
python3 --version
# Should show: Python 3.11.x or higher
```

If you see "command not found", install Python:
```bash
brew install python@3.11
```

## Troubleshooting

**If `python3` is not found:**
- Install Python via Homebrew: `brew install python@3.11`
- Or download from https://www.python.org/downloads/

**If `pip3` is not found:**
- Python 3.4+ includes pip by default
- If missing: `python3 -m ensurepip --upgrade`

**If venv creation fails:**
- Check permissions: `ls -la` in backend directory
- Try: `python3 -m venv --help` to verify venv module exists
- On macOS, you might need to allow full disk access for Terminal

**Permission errors:**
- Make sure you're not in a restricted directory
- Try running outside of any IDE terminal (use regular Terminal app)

## Recommended: Use Docker Instead

The easiest way to avoid all Python setup issues is to use Docker:

```bash
# From project root
docker-compose up --build
```

This handles all dependencies automatically and works the same way on any system!
