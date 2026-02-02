@echo off
REM Run all tests on Windows

echo ================================
echo Running Test Suite
echo ================================
echo.

REM Run unit tests
echo 1. Running Unit Tests...
echo ------------------------
pytest tests/unit/ -v -m unit
echo.

REM Run integration tests
echo 2. Running Integration Tests...
echo --------------------------------
pytest tests/integration/ -v -m integration
echo.

REM Run existing tests
echo 3. Running Existing Tests...
echo ----------------------------
pytest tests/test_*.py -v
echo.

REM Run E2E tests (may be slow)
echo 4. Running E2E Tests...
echo -----------------------
pytest tests/e2e/ -v -m e2e --timeout=300
echo.

echo ================================
echo Test Suite Complete
echo ================================
