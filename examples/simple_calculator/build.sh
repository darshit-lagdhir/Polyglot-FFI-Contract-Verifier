# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 3adaae8ebf33b4d8
# ==============================================================================

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