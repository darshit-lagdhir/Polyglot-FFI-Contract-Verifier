@echo off
REM install.bat - Windows installation script

echo ======================================
echo Polyglot FFI Verifier - Install
echo ======================================
echo.

REM Check Python version
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)

REM Check Python version is 3.11+
python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11+ required
    exit /b 1
)

echo [1/4] Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install libclang
)

echo [2/4] Installing development dependencies...
if exist requirements-dev.txt (
    pip install -r requirements-dev.txt
) else (
    pip install pytest pytest-cov pytest-timeout black flake8 mypy
)

echo [3/4] Installing package in editable mode...
pip install -e .

echo [4/4] Verifying installation...
polyglot-verify --help >NUL
if errorlevel 1 (
    echo Warning: polyglot-verify command not yet in PATH.
    echo Please ensure the Python Scripts folder is in your PATH.
) else (
    echo polyglot-verify command is available.
)

echo.
echo ======================================
echo Install Complete!
echo ======================================
echo.
echo Try: polyglot-verify --help
