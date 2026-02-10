# Polyglot FFI Contract Verifier - User Guide

Complete guide to using the FFI verification pipeline.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Usage](#advanced-usage)
4. [Performance Tuning](#performance-tuning)
5. [Best Practices](#best-practices)
6. [Diagnostics](#troubleshooting)
7. [Common Issues](#faq)

---
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

---

# Advanced Usage Guide

Beyond basic verification, Module 02 provides advanced features for
power users and integration scenarios.

## Table of Contents

1. [Custom Constraints](2. [Plugin Development](#plugin-development)
3. [Performance Optimization](#performance-optimization)
4. [CI/CD Integration](#cicd-integration)
5. [Incremental Verification](#incremental-verification)
6. [Parallel Execution](#parallel-execution)

---


Define domain-specific constraints for your FFI interfaces.


```python
from modules.module_02_verification_pipeline.verification_pipeline import CustomConstraint

class SIMDAlignmentConstraint(CustomConstraint):
    """Enforce 16-byte alignment for SIMD operations."""
    
    CONSTRAINT_TYPE = "simd_alignment"
    
    def __init__(self, target: str):
        super().__init__("simd_alignment", target)
        self.alignment = 16
    
    def validate(self, value: int) -> bool:
        """Check if pointer is 16-byte aligned."""
        if value is None:
            return True
        return (value % self.alignment) == 0
    
    def generate_check_code(self) -> str:
        """Generate runtime check code."""
        return f"""
if {self.target} is not None:
    addr = ctypes.cast({self.target}, ctypes.c_void_p).value
    if (addr % 16) != 0:
        raise ContractViolation(
            "SIMD pointer must be 16-byte aligned"
        )
"""

# Use in verification
result = verify_extensible(
    "graphics.h", "graphics.dll",
    custom_rules={
        "simd_vectors": {
            "constraint_class": SIMDAlignmentConstraint,
            "synthesis_heuristic": lambda p: "simd_" in p.name
        }
    }
)
```

## 2. Plugin Development

Create reusable plugins for domain-specific verification.

### Example: Windows API Plugin
```python
from modules.module_02_verification_pipeline.verification_pipeline import PipelinePlugin

class WindowsAPIPlugin(PipelinePlugin):
    """Plugin for Windows-specific API verification."""
    
    PLUGIN_NAME = "windows_api"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_AUTHOR = "Your Authors"
    
    def initialize(self, pipeline):
        """Initialize plugin with pipeline."""
        self.pipeline = pipeline
    
    def register_rules(self, registry):
        """Register Windows-specific rules."""
        # HANDLE must not be INVALID_HANDLE_VALUE (-1)
        registry.register(
            "handle_valid",
            HandleValidConstraint,
            lambda p: "HANDLE" in str(p.type)
        )
        
        # LPCWSTR must be null-terminated
        registry.register(
            "lpcwstr_terminated",
            NullTerminatedConstraint,
            lambda p: "LPCWSTR" in str(p.type)
        )
    
    def get_hooks(self):
        """Register lifecycle hooks."""
        return {
            "post_contract_synthesis": self.add_win32_metadata
        }
    
    def add_win32_metadata(self, context, contract):
        """Add Windows-specific metadata to contract."""
        for func in contract["functions"]:
            if func["name"].startswith("Create"):
                func["metadata"] = {"requires_elevation": True}

# Use plugin
result = verify_extensible(
    "winapi.h", "kernel32.dll",
    plugins=[WindowsAPIPlugin()]
)
```

## 3. Performance Optimization

Optimize verification for large codebases.

### 3.1 Enable Caching
```python
result = verify_optimized(
    "large_api.h", "large_lib.dll",
    cache=True,              # Enable caching
    cache_dir=".cache"       # Custom cache directory
)
# First run: 180 seconds
# Second run: 45 seconds (4x speedup)
```

### 3.2 Parallel Execution
```python
result = verify_optimized(
    "large_api.h", "large_lib.dll",
    parallel=True,           # Enable parallelism
    max_workers=8            # Use 8 CPU cores
)
# Sequential: 180 seconds
# Parallel: 90 seconds (2x speedup)
```

### 3.3 Incremental Verification
```python
# After modifying contract manually
result = verify_optimized(
    "api.h", "lib.dll",
    incremental=True,        # Only re-run affected stages
    reuse_artifacts=True
)
# Only stages 4-7 re-execute
```

### 3.4 Profiling
```python
result = verify_optimized(
    "api.h", "lib.dll",
    profile=True             # Enable profiling
)
# Generates performance.prof
```
View profile:
```bash
python -m pstats performance.prof
```

## 4. CI/CD Integration

### GitHub Actions Example
```yaml
name: FFI Verification

on: [push, pull_request]

jobs:
  verify:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run verification
        run: |
          python -c "
          from modules.module_02_verification_pipeline.verification_pipeline import verify
          result = verify('interface.h', 'library.dll')
          exit(0 if result.success else 1)
          "
      
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: verification-report
          path: artifacts/report.html
```

### GitLab CI Example
```yaml
ffi-verification:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python verify_ci.py
  artifacts:
    when: always
    paths:
      - artifacts/report.html
    reports:
      junit: artifacts/junit.xml
```

## 5. Incremental Verification

Optimize verification during development.

### Workflow
```bash
# Initial run (full verification)
python verify.py --output run1/

# Modify contract manually
vim run1/contract.json

# Re-run only affected stages
python verify.py --output run2/ --incremental --from=adapter_generation
```

### Programmatic
```python
# First run
result1 = verify("api.h", "lib.dll", output_dir="run1")

# Modify contract
import json
with open("run1/contract.json", "r+") as f:
    contract = json.load(f)
    # Modify contract...
    f.seek(0)
    json.dump(contract, f)

# Incremental re-run
result2 = verify(
    "api.h", "lib.dll",
    output_dir="run2",
    reuse_artifacts="run1",
    start_from="adapter_generation"
)
```

## 6. Parallel Execution

Leverage multi-core systems.

### Automatic Parallelism
```python
result = verify_optimized(
    "api.h", "lib.dll",
    parallel=True,
    max_workers=None  # Use all CPU cores
)
```

### Manual Control
```python
from modules.module_02_verification_pipeline.verification_pipeline import (
    CompletePipeline,
    ParallelPipelineExecutor
)

pipeline = CompletePipeline("api.h", "lib.dll")
executor = ParallelPipelineExecutor(pipeline, max_workers=4)
success = executor.execute_parallel()
```

## Best Practices
- Enable caching for repeated verifications
- Use parallel execution for large codebases
- Profile bottlenecks with `profile=True`
- Custom plugins for domain-specific patterns
- CI/CD integration for continuous verification
- Incremental updates during development

**See Also:**
- [Performance Tuning Guide](PERFORMANCE_TUNING.md)
- [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)
- [API Reference](API_REFERENCE_AUTO.md)

---

# Performance Tuning Guide

Optimize Module 02 for speed and resource efficiency.

## Benchmarks

Reference performance on standard hardware (8-core, 16GB RAM):

| Library Size | Functions | Time (Cold) | Time (Cached) | Speedup |
|--------------|-----------|-------------|---------------|---------|
| Small        | 5         | 8.5s        | 3.2s          | 2.7x    |
| Medium       | 50        | 45s         | 18s           | 2.5x    |
| Large        | 200       | 180s        | 75s           | 2.4x    |

## Optimization Strategies

### 1. Caching (Highest Impact)

**Problem:** Re-running unchanged verification wastes time.

**Solution:** Enable artifact caching.

```python
result = verify_optimized("api.h", "lib.dll", cache=True)
```
**Impact:** 2-3x speedup on repeated runs.

**Caveats:**
- First run still slow (cold cache)
- Cache invalidates on file changes
- Uses ~500MB disk space per project

### 2. Parallel Execution (Medium Impact)

**Problem:** Stages run sequentially even when independent.

**Solution:** Enable parallel execution.

```python
result = verify_optimized(
    "api.h", "lib.dll",
    parallel=True,
    max_workers=8
)
```
**Impact:** 1.5-2x speedup (depends on stage dependencies).

**Caveats:**
- Limited by dependencies (not all stages can parallelize)
- Diminishing returns beyond 4-8 workers
- Higher memory usage

### 3. Incremental Updates (High Impact for Development)

**Problem:** Re-running full pipeline after small changes.

**Solution:** Re-run only affected stages.

```python
result = verify(
    "api.h", "lib.dll",
    start_from="adapter_generation",
    reuse_artifacts="previous_run/"
)
```
**Impact:** 3-10x speedup when only late stages need updates.

### 4. Reduce Test Cases (Trade-off)

**Problem:** 1000+ test cases take long to execute.

**Solution:** Reduce test generation.

```python
# Custom test plan with fewer tests
result = verify_extensible(
    "api.h", "lib.dll",
    hooks={
        "post_test_plan_generation": lambda ctx, plan: 
            plan["test_cases"][:100]  # Only first 100 tests
    }
)
```
**Impact:** Proportional speedup (50% fewer tests = 50% faster).

**Trade-off:** Lower coverage.

## Memory Optimization

### Streaming Large Artifacts
For artifacts >100MB, use streaming:

```python
# Automatically enables for large files
result = verify_optimized(
    "huge_api.h", "huge_lib.dll",
    streaming_threshold_mb=100
)
```

### Garbage Collection Tuning
```python
import gc

# Disable during verification
gc.disable()
result = verify("api.h", "lib.dll")
gc.collect()  # Manual collection after
```
**Impact:** 10-15% speedup, but higher peak memory.

## Profiling

Identify bottlenecks:

```python
result = verify_optimized("api.h", "lib.dll", profile=True)
```
View results:
```bash
python -m pstats performance.prof
```
**Common bottlenecks:**
- libclang parsing (Stage 1): 30-40% of time
- Test execution (Stage 6): 40-50% of time
- Type resolution (Stage 2): 10-15% of time

## Hardware Recommendations

| Use Case | CPU | RAM | Disk |
|----------|-----|-----|------|
| Small projects | 2 cores | 4GB | SSD |
| Medium projects | 4 cores | 8GB | SSD |
| Large projects | 8+ cores | 16GB+ | NVMe SSD |
| CI/CD | 4 cores | 8GB | SSD |

## CI/CD Optimization

```yaml
# Use caching in CI
- name: Cache verification artifacts
  uses: actions/cache@v3
  with:
    path: .verification_cache
    key: ${{ hashFiles('*.h') }}-${{ hashFiles('*.dll') }}

- name: Run verification
  run: python verify.py --cache
```

**Next:** [Advanced Usage](ADVANCED_USAGE.md)

---

# Best Practices

Recommended patterns for effective FFI verification.

## General Principles

### 1. Start Simple

Begin with basic verification, then add customization:

```python
# First run: Basic verification
result = verify("interface.h", "library.dll")

# Later: Add optimizations
result = verify_optimized("interface.h", "library.dll", cache=True)

# Advanced: Add custom rules
result = verify_extensible("interface.h", "library.dll", plugins=[...])
```

### 2. Verify Early and Often

Integrate verification into development workflow:

- Run verification on every commit
- Include in CI/CD pipeline
- Verify before releases

### 3. Review Reports Carefully

Don't just check pass/fail:

- Understand why tests failed
- Review constraint coverage
- Check for missing edge cases

---

## Header Design

### Use Explicit Contracts

**Bad:**
```c
void process(char* data, int size);
```

**Good:**
```c
// Processes data buffer
// @param data: Non-null buffer of at least 'size' bytes
// @param size: Buffer size, must be > 0
void process(char* data, int size);
```

### Avoid Implicit Assumptions

**Bad:**
```c
int get_value(void* context);  // What is context
```

**Good:**
```c
typedef struct Config Config;
int get_value(Config* config);  // Clear type
```

### Use `const` Appropriately

```c
// Input parameter - use const
int process(const char* input, size_t length);

// Output parameter - no const
int read_data(char* output, size_t* length);
```

---

## Performance Optimization

### Enable Caching for Iterative Development

```python
# During development (fast iteration)
result = verify_optimized("interface.h", "library.dll", cache=True)
```

Cache invalidation happens automatically when:
- Header file changes
- Library file changes
- Pipeline version changes

### Use Parallelism for Large Codebases

```python
# For headers with 50+ functions
result = verify_optimized(
    "large_interface.h", "library.dll",
    parallel=True,
    max_workers=8  # Match CPU cores
)
```

### Profile to Identify Bottlenecks

```python
result = verify_optimized("interface.h", "library.dll", profile=True)
# Check performance.prof for slow stages
```

---

## Customization

### Create Reusable Plugins

Package domain-specific rules as plugins:

```python
# my_plugin.py
from verification_pipeline import PipelinePlugin

class DomainPlugin(PipelinePlugin):
    PLUGIN_NAME = "domain_rules"
    PLUGIN_VERSION = "1.0.0"
    
    def register_rules(self, registry):
                pass
```

Use across projects:
```python
from my_plugin import DomainPlugin

result = verify_extensible(
    "interface.h", "library.dll",
    plugins=[DomainPlugin()]
)
```

### Use Hooks for Custom Logic

```python
def log_contract(context, contract, **kwargs):
    """Log synthesized contract for review."""
    with open("contract_review.json", "w") as f:
        json.dump(contract, f, indent=2)

result = verify_extensible(
    "interface.h", "library.dll",
    hooks={"post_contract_synthesis": log_contract}
)
```

---

## CI/CD Integration


```python
result = verify("interface.h", "library.dll")

if result.critical_issues:
    print("CRITICAL ISSUES:")
    for issue in result.critical_issues:
        print(f"  - {issue}")
    sys.exit(1)
```

### Upload Reports as Artifacts

**GitHub Actions:**
```yaml
- name: Run verification
  run: python verify.py

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v2
  with:
    name: verification-report
    path: artifacts/report.html
```

### Cache Verification Results

```yaml
- name: Cache verification
  uses: actions/cache@v2
  with:
    path: .verification_cache
    key: verification-${{ hashFiles('interface.h') }}
```

---

## Testing Strategy

### Test Positive and Negative Cases

Verification generates both:
- **Positive tests**: Valid inputs should succeed
- **Negative tests**: Invalid inputs should fail safely

Review both in the report.

### Supplement with Manual Tests

Verification is comprehensive but not exhaustive:

```python
# After verification, add manual edge cases
def test_my_edge_case():
    # Custom test logic
    pass
```

### Monitor Coverage

Check constraint coverage in report:
- Aim for >80% coverage
- Identify untested constraints
- Add custom tests for gaps

---


### Keep Documentation Updated

When interface changes:
1. Update header comments
2. Re-run verification
3. Review new constraints
4. Update custom rules if needed

### Version Your Plugins

```python
class MyPlugin(PipelinePlugin):
    PLUGIN_VERSION = "1.2.0"  # Increment on changes
```

### Review Verification Regularly

Schedule periodic reviews:
- Monthly: Check for new edge cases
- Quarterly: Review custom rules
- Yearly: Audit entire verification setup

---

## Common Patterns

### Buffer + Length Pattern

```c
int process_buffer(const char* data, size_t length);
```

Verification automatically infers:
- `data` must not be null if `length > 0`
- `data` must point to buffer of at least `length` bytes

### Output Parameter Pattern

```c
int get_data(char** output, size_t* length);
```

Verification infers:
- `output` must not be null
- `length` must not be null
- Function allocates memory (caller must free)

### Handle Pattern

```c
typedef void* HANDLE;
int create_handle(HANDLE* handle);
int close_handle(HANDLE handle);
```

Add custom constraint:
```python
class HandleValidConstraint(CustomConstraint):
    def validate(self, value):
        return value is not None and value != -1
```

---

## Anti-Patterns to Avoid


Don't just disable failing tests. Investigate and fix.

### ❌ Over-Customizing

Start with default behavior. Only customize when necessary.

### ❌ Not Reviewing Reports

The HTML report contains valuable insights. Always review it.

### ❌ Skipping Verification in CI

Verification should be part of every build.

---

## Summary

**Do:**
- ✓ Verify early and often
- ✓ Review reports carefully
- ✓ Use caching for speed
- ✓ Create reusable plugins
- ✓ Integrate with CI/CD

**Don't:**
- ✗ Ignore failures
- ✗ Over-customize
- ✗ Skip CI verification
- ✗ Forget to update docs

---

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

---

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

