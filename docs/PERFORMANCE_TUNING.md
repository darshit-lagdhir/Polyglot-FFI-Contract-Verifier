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
