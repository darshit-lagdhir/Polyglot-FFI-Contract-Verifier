# Quick Start Guide

Get FFI verification running in 5 minutes.

## Install

```bash
pip install polyglot-ffi-verifier
```

## Basic Usage

### : Prepare Your Code

You need:
- C header file (`.h`)
- Compiled library (`.dll`, `.so`, `.dylib`)

Example `calculator.h`:

```c
int add(int a, int b);
int divide(int a, int b);
```

### : Run Verification

```python
from verification_pipeline import verify

result = verify("calculator.h", "calculator.dll")

if result.success:
    print(f"✓ Verification passed: {result.pass_rate}%")
else:
    print(f"✗ Verification failed: {len(result.critical_issues)} issues")
    print(f"Report: {result.report_path}")
```

### : Review Report

Open the HTML report:

```bash
open artifacts/report.html
```

The report shows:
- ✓ Tests that passed
- ✗ Tests that failed
- Specific recommendations for each failure

## Next Steps

- [Complete Tutorial](tutorials/01_basic_verification.md)
- [User Guide](user_guide.md)
- [API Reference](api_reference.md)
