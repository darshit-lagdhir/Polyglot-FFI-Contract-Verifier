# Advanced Usage Guide

Beyond basic verification, Module 02 provides advanced features for
power users and integration scenarios.

## Table of Contents

1. [Custom Constraints](#custom-constraints)
2. [Plugin Development](#plugin-development)
3. [Performance Optimization](#performance-optimization)
4. [CI/CD Integration](#cicd-integration)
5. [Incremental Verification](#incremental-verification)
6. [Parallel Execution](#parallel-execution)

---

## 1. Custom Constraints

Define domain-specific constraints for your FFI interfaces.

### Example: SIMD Alignment Constraint

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
