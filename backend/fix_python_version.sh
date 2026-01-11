#!/bin/bash

# Script to fix Python version issue
# This will install Python 3.11 and recreate the virtual environment

set -e

echo "🔧 Fixing Python version issue..."
echo ""

# Step 1: Install Python 3.11 if not already installed
echo "Step 1: Checking if Python 3.11 is installed..."
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Installing via Homebrew..."
    brew install python@3.11
    echo "✅ Python 3.11 installed!"
else
    echo "✅ Python 3.11 is already installed"
fi

# Step 2: Remove old venv
echo ""
echo "Step 2: Removing old virtual environment (Python 3.13)..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "✅ Old venv removed"
else
    echo "No old venv found"
fi

# Step 3: Deactivate if currently activated
echo ""
echo "Step 3: Creating new virtual environment with Python 3.11..."
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating current venv..."
    deactivate 2>/dev/null || true
fi

# Step 4: Create new venv with Python 3.11
python3.11 -m venv venv
echo "✅ New venv created with Python 3.11"

# Step 5: Activate venv
echo ""
echo "Step 4: Activating virtual environment..."
source venv/bin/activate

# Step 6: Upgrade pip
echo ""
echo "Step 5: Upgrading pip..."
pip install --upgrade pip

# Step 7: Install requirements
echo ""
echo "Step 6: Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt

echo ""
echo "✅✅✅ SUCCESS! ✅✅✅"
echo ""
echo "Virtual environment is ready with Python 3.11!"
echo ""
echo "To activate it in the future, run:"
echo "  cd /Users/ravikantpandit/koodsisu/ghostwriter/backend"
echo "  source venv/bin/activate"
echo ""
echo "To run the server:"
echo "  export OPENAI_API_KEY=your_key_here"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
