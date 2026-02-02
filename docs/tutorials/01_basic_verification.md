# Tutorial 01: Basic Verification

Learn FFI verification with a complete example.

## Overview

This tutorial demonstrates:
- Setting up a simple C library
- Running verification
- Understanding results
- Fixing issues

**Time:** 15 minutes

---

## : Create C Library

Create `calculator.h`:

```c
#ifndef CALCULATOR_H
#define CALCULATOR_H

// Add two integers
int add(int a, int b);

// Divide two integers
// Returns 0 if b is zero
int divide(int a, int b);

#endif
```

Create `calculator.c`:

```c
#include "calculator.h"

int add(int a, int b) {
    return a + b;
}

int divide(int a, int b) {
    if (b == 0) return 0;
    return a / b;
}
```

---

## : Compile Library

**Windows (MSVC):**
```bash
cl /LD calculator.c /Fe:calculator.dll
```

**Linux (GCC):**
```bash
gcc -shared -fPIC calculator.c -o libcalculator.so
```

**macOS (Clang):**
```bash
clang -shared -fPIC calculator.c -o libcalculator.dylib
```

---

## : Run Verification

Create `verify.py`:

```python
import sys
from verification_pipeline import verify

# Determine library name
if sys.platform == "win32":
    library = "calculator.dll"
elif sys.platform == "darwin":
    library = "libcalculator.dylib"
else:
    library = "libcalculator.so"

# Run verification
result = verify("calculator.h", library)

# Print results
print(result)

# Exit with appropriate code
sys.exit(0 if result.success else 1)
```

Run it:
```bash
python verify.py
```

---

## : Understand Output

You should see:

```
[Stage 1/7] Native Interface Ingestion... ✓
[Stage 2/7] IR Normalization... ✓
[Stage 3/7] Contract Synthesis... ✓
[Stage 4/7] Adapter Generation... ✓
[Stage 5/7] Test Plan Generation... ✓
[Stage 6/7] Verification Execution... ✓
[Stage 7/7] Diagnostics & Reporting... ✓

Verification Result:
  Status: PASS
  Pass Rate: 100.0%
  Tests: 8 passed, 0 failed
  Time: 2.3s
  Report: artifacts/report.html
```

---

## : Review Report

Open `artifacts/report.html` in your browser.

The report shows:

### Executive Summary
- Overall status: **PASS**
- Pass rate: **100%**
- Total tests: **8**

### Test Results

| Test | Category | Result |
|------|----------|--------|
| add_positive_values | Positive | ✓ PASS |
| add_negative_values | Positive | ✓ PASS |
| add_zero | Boundary | ✓ PASS |
| add_overflow | Boundary | ✓ PASS |
| divide_normal | Positive | ✓ PASS |
| divide_by_zero | Negative | ✓ PASS |
| divide_zero_numerator | Boundary | ✓ PASS |
| divide_negative | Positive | ✓ PASS |

### Constraint Coverage

- **add()**: 2 constraints tested (100%)
- **divide()**: 3 constraints tested (100%)

---

## : Introduce a Bug

Modify `calculator.c` to introduce a bug:

```c
int divide(int a, int b) {
    // BUG: Removed zero check!
    return a / b;
}
```

Recompile and re-run verification:

```bash
# Recompile
cl /LD calculator.c /Fe:calculator.dll  # Windows
gcc -shared -fPIC calculator.c -o libcalculator.so  # Linux

# Verify again
python verify.py
```

---

## : Understand Failure

Now you should see:

```
Verification Result:
  Status: FAIL
  Pass Rate: 87.5%
  Tests: 7 passed, 1 failed
  Critical Issues: 1
  Report: artifacts/report.html
```

Open the report. The failed test shows:

**Test:** `divide_by_zero`  
**Category:** Negative  
**Result:** ✗ FAIL  
**Error:** `ZeroDivisionError: division by zero`

**Recommendation:**
```
The function 'divide' does not handle division by zero.
Add a check: if (b == 0) return error_value;
```

---

## : Fix the Bug

Restore the zero check:

```c
int divide(int a, int b) {
    if (b == 0) return 0;  // Fixed!
    return a / b;
}
```

Recompile and verify again. Should pass!

---

## What You Learned

✓ How to set up verification  
✓ How to run verification  
✓ How to read results  
✓ How verification catches bugs  
✓ How to fix issues  

---

## Next Steps

- [Tutorial 02: Custom Rules](02_custom_rules.md)
- [Tutorial 03: Plugins](03_plugins.md)
- [User Guide](../user_guide.md)
