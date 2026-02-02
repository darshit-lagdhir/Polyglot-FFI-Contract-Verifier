# Frequently Asked Support

## Install

**Q: Import error: "No module named 'clang'"**

A: Install libclang:
```bash
pip install libclang
```
If still fails, set `LIBCLANG_PATH`:
```bash
export LIBCLANG_PATH=/usr/lib/llvm-16/lib/libclang.so
```

**Q: "IDE required" error on Windows**

A: Install Build Tools:
1. Download from: https://visualstudio.microsoft.com/downloads/
2. Select "Desktop development with C++"
3. Or use pre-built examples

## Usage

**Q: Verification fails with "Header compilation error"**

A: Check compiler flags:
```python
result = verify(
    "interface.h", "library.dll",
    compiler_flags=["-I/usr/include", "-DWIN32"]
)
```

**Q: How do I verify only specific functions**

A: Use custom test plan hooks:
```python
result = verify_extensible(
    "api.h", "lib.dll",
    hooks={
        "post_test_plan_generation": 
            lambda ctx, plan: filter_tests(plan, ["func1", "func2"])
    }
)
```

## Performance

**Q: Verification is slow (>5 minutes)**

A: Enable caching and parallelism:
```python
result = verify_optimized(
    "api.h", "lib.dll",
    cache=True,
    parallel=True
)
```

**Q: High memory usage (>2GB)**

A: Enable streaming for large artifacts:
```python
result = verify_optimized(
    "api.h", "lib.dll",
    streaming_threshold_mb=50
)
```

## Errors

**Q: "Stage failed: contract_synthesis"**

A: Common causes:
- Complex types (manual annotation needed)
- Missing type definitions
- Circular dependencies

Solution: Add manual constraints:
```json
// contract.json
{
  "functions": [{
    "name": "problematic_func",
    "constraints": [
      {"type": "NON_NULL", "target": "param_data"}
    ]
  }]
}
```

**Q: Tests fail but code works**

A: This might be a false positive. Adjust your contract or heuristics:
```python
# Mark parameter as nullable
result = verify_extensible(
    "api.h", "lib.dll",
    custom_rules={
        "optional_ptr": {
            "constraint_class": NullableConstraint,
            "synthesis_heuristic": lambda p: "optional" in p.name
        }
    }
)
```

## Module Integration

**Q: How do I use Module 02 from another module**

A: 
```python
from modules.module_02_verification_pipeline.verification_pipeline import verify

result = verify("interface.h", "library.dll")
```

**Q: Can I reuse artifacts in Module 03**

A: Yes, Module 03 consumes:
- `contract.json`: for formal verification
- `ir.json`: for symbolic execution
- `test_plan.json`: for concrete test cases

Still having issues Open an issue: https://github.com/darshit-lagdhir/polyglot-ffi-verifier/issues
