@echo off
REM Build script for Windows (MSVC)

echo Building calculator.dll...

cl /LD /O2 calculator.c /Fe:calculator.dll

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful: calculator.dll
    echo.
    echo Run verification with:
    echo   python verify.py
) else (
    echo.
    echo Build failed!
    echo.
    echo Make sure you have MSVC installed and run this from
    echo a IDE Developer Command Prompt.
)
