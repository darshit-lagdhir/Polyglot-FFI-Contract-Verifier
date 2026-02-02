# Diagnostics Guide

Common issues and solutions for FFI verification.

## Install Issues

### libclang not found

**Error:**
```
ImportError: libclang.so not found
```

**Solution:**

**Linux:**
```bash
sudo apt-get install libclang-dev
export LD_LIBRARY_PATH=/usr/lib/llvm-14/lib:$LD_LIBRARY_PATH
```

**macOS:**
```bash
brew install llvm
export DYLD_LIBRARY_PATH=/usr/local/opt/llvm/lib:$DYLD_LIBRARY_PATH
```

**Windows:**
Download LLVM from https://llvm.org/builds/ and add to PATH.

---

## Verification Errors

### Header parsing failed

**Error:**
```
StageError: Native Interface Ingestion failed
```

**Possible causes:**
1. Missing include paths
2. Syntax errors in header
3. Unsupported C features

**Solution:**

Add compiler flags:
```python
result = verify(
    "interface.h", "library.dll",
    compiler_flags=["-I/usr/include", "-DWIN32"]
)
```

---

### Library loading failed

**Error:**
```
OSError: library.dll not found
```

**Solution:**

1. Check library path is correct
2. Ensure library is compiled for your platform
3. Check dependencies are available

**Windows:**
```bash
dumpbin /dependents library.dll
```

**Linux:**
```bash
ldd library.so
```

---

### All tests failing

**Possible causes:**
1. Incorrect calling convention
2. Name mangling (C++ vs C)
3. ABI mismatch

**Solution:**

Ensure header uses `extern "C"`:
```c
#ifdef __cplusplus
extern "C" {
#endif

// Functions here

#ifdef __cplusplus
}
#endif
```

---

## Performance Issues

### Verification is slow

**Solutions:**

1. **Enable caching:**
```python
result = verify_optimized("interface.h", "library.dll", cache=True)
```

2. **Enable parallelism:**
```python
result = verify_optimized(
    "interface.h", "library.dll",
    parallel=True,
    max_workers=8
)
```

3. **Profile to find bottlenecks:**
```python
result = verify_optimized("interface.h", "library.dll", profile=True)
```

---

## Test Failures

### False positives

**Issue:** Tests fail but code is correct.

**Solution:**

Add custom constraints to refine contract:
```python
from verification_pipeline import CustomConstraint

class MyConstraint(CustomConstraint):
    def validate(self, value):
        # Your checker logic
        return True
```

---

### Missing edge cases

**Issue:** Tests don't cover important scenarios.

**Solution:**

Use hooks to inject custom tests:
```python
def add_custom_tests(context, test_plan, **kwargs):
    test_plan["test_cases"].append({
        "name": "my_edge_case",
        "inputs": {...},
        "expected": {...}
    })

result = verify_extensible(
    "interface.h", "library.dll",
    hooks={"post_test_plan_generation": add_custom_tests}
)
```

---

## Getting Help

If you encounter issues not covered here:

1. Check the [User Guide](user_guide.md)
2. Review [Examples](../examples/)
3. Open an issue on GitHub
4. Contact support
