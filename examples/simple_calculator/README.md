<!-- ============================================================================== -->
<!-- Polyglot FFI Contract Verifier -->
<!-- Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved. -->
<!--  -->
<!-- This file is part of the Polyglot FFI Contract Verifier ecosystem. -->
<!-- It is licensed under the Antigravity Source-Available and Technical  -->
<!-- Protection License (ASTPL). -->
<!--  -->
<!-- PROHIBITED USES: Commercial Use, Network Access Provision, and Machine  -->
<!-- Training Use are strictly prohibited absent explicit written authorization. -->
<!--  -->
<!-- Removal or alteration of this header may constitute a violation of the  -->
<!-- repository's governing agreements. -->
<!--  -->
<!-- File Integrity Identifier: 11f988038e5be1f6 -->
<!-- ============================================================================== -->

# Simple Calculator Example

Complete working example of FFI verification.

## Overview

This example demonstrates basic FFI verification with a simple calculator library.

## Files

- `calculator.h` - C header
- `calculator.c` - C implementation  
- `build.bat` - Build script (Windows)
- `build.sh` - Build script (Linux/macOS)
- `verify.py` - Verification script

## Build

**Windows:**
```bash
build.bat
```

**Linux/macOS:**
```bash
chmod +x build.sh
./build.sh
```

## Verify

```bash
python verify.py
```

## Expected Results

- 15 tests generated
- All tests pass
- 100% pass rate

## What This Example Shows

- Basic function verification
- Buffer handling
- Divide-by-zero handling
- Null pointer handling
- Boundary value testing


### calculator.h

Defines the C interface with 5 functions:
- `add()` - Addition
- `subtract()` - Subtraction
- `multiply()` - Multiplication
- `divide()` - Division (handles zero)
- `sum_buffer()` - Buffer processing

### calculator.c

Implements the functions with proper error handling.

### verify.py

Runs verification and reports results.

## Try It Yourself

1. Build the library
2. Run verification
3. Introduce a bug (remove zero check in `divide`)
4. See verification catch it!
5. Fix the bug
6. Verify again