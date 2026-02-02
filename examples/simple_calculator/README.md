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

## Files Explained

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
