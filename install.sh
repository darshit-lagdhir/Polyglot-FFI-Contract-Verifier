#!/bin/bash
# install.sh - Unix installation script

set -e

echo "======================================"
echo "Polyglot FFI Verifier - Install"
echo "======================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

# Check version
python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" || {
    echo "ERROR: Python 3.11+ required"
    exit 1
}

echo "[1/5] Installing system dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Try to install libclang-dev if possible, or just print a reminder
    echo "Important: You may need to run 'sudo apt-get install -y libclang-dev'"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Important: You may need to run 'brew install llvm'"
fi

echo "[2/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[3/5] Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install libclang
fi

echo "[4/5] Installing package..."
pip install -e .

echo "[5/5] Verifying installation..."
if command -v polyglot-verify &> /dev/null; then
    polyglot-verify --help > /dev/null
    echo "polyglot-verify command is available."
else
    echo "Warning: polyglot-verify not found in PATH."
fi

echo ""
echo "======================================"
echo "Install Complete!"
echo "======================================"
echo ""
echo "Activate venv: source venv/bin/activate"
echo "Try: polyglot-verify --help"
