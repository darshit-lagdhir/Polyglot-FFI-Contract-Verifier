#!/bin/bash
# Build script for Linux/macOS

echo "Building calculator library..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    clang -shared -fPIC -O2 calculator.c -o libcalculator.dylib
    LIBRARY="libcalculator.dylib"
else
    # Linux
    gcc -shared -fPIC -O2 calculator.c -o libcalculator.so
    LIBRARY="libcalculator.so"
fi

if [ $ -eq 0 ]; then
    echo ""
    echo "Build successful: $LIBRARY"
    echo ""
    echo "Run verification with:"
    echo "  python verify.py"
else
    echo ""
    echo "Build failed!"
    echo ""
    echo "Make sure you have gcc/clang installed."
fi
