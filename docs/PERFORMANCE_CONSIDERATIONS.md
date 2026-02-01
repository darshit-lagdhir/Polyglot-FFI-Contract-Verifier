# Performance Considerations

## Overview
The Polyglot FFI Contract Verifier is designed for development-time and CI
verification, not runtime production use. Performance is adequate for typical
verification workloads but not optimized for high-throughput scenarios.

## Performance Characteristics

### : Orchestration
- **Time Complexity:** O(1)
- **Space Complexity:** O(1)
- **Typical Duration:** < 100ms
- **Bottlenecks:** None

### : Native Interface Ingestion
- **Time Complexity:** O(n) where n = number of declarations in header
- **Space Complexity:** O(n)
- **Typical Duration:** 500ms - 5s depending on header complexity
- **Bottlenecks:** 
  * libclang parsing (dependent on header size and complexity)
  * Macro expansion (can be expensive for heavily templated headers)
  * Include resolution (dependent on number of includes)

**Optimization Strategies:**
- Minimize include depth where possible
- Use precompiled headers if available
- Cache native_interface.json to avoid re-ingestion

### : IR Normalization
- **Time Complexity:** O(n) where n = number of types
- **Space Complexity:** O(n)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Typedef resolution (recursive traversal)
  * Type registry construction

### : Contract Synthesis
- **Time Complexity:** O(f * c) where f = functions, c = constraints per function
- **Space Complexity:** O(f * c)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * Constraint derivation rules (10 rules per function)
  * Naming convention analysis (pattern matching)

### : Contract Versioning
- **Time Complexity:** O(c1 + c2) where c = constraints in each contract
- **Space Complexity:** O(c1 + c2)
- **Typical Duration:** 50ms - 500ms
- **Bottlenecks:** 
  * Deep comparison of contract structures

### : Adapter Generation
- **Time Complexity:** O(f + s) where f = functions, s = structs
- **Space Complexity:** O(f + s)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Code generation (template rendering)
  * File I/O (writing multiple adapter modules)

### : Test Plan Generation
- **Time Complexity:** O(c * t) where c = constraints, t = tests per constraint
- **Space Complexity:** O(c * t)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * Input value generation (deterministic but computationally intensive)
  * Coverage analysis

### : Verification Execution
- **Time Complexity:** O(t * e) where t = tests, e = execution time per test
- **Space Complexity:** O(t)
- **Typical Duration:** 5s - 5min depending on test count
- **Bottlenecks:**
  * Test execution (calling native library repeatedly)
  * Serialization/deserialization overhead

**Critical Performance Factor:** This is the slowest phase by far.

### : Runtime Monitoring
- **Time Complexity:** O(t) where t = tests
- **Space Complexity:** O(t)
- **Typical Duration:** +20-50% overhead over 
- **Bottlenecks:**
  * Subprocess spawning (expensive on Windows)
  * IPC overhead (serialization between parent/child)

**Optimization Strategies:**
- Reuse subprocesses where possible (future improvement)
- Minimize serialization overhead
- Run tests in parallel (future improvement)

### 0: Diagnostics Mapping
- **Time Complexity:** O(v) where v = violations
- **Space Complexity:** O(v)
- **Typical Duration:** 100ms - 1s
- **Bottlenecks:**
  * Root cause analysis heuristics
  * Violation aggregation

### 1: Report Generation
- **Time Complexity:** O(v) where v = violations
- **Space Complexity:** O(v)
- **Typical Duration:** 200ms - 2s
- **Bottlenecks:**
  * HTML rendering (template expansion)
  * CSS embedding

### 2: CI Integration
- **Time Complexity:** O(1)
- **Space Complexity:** O(1)
- **Typical Duration:** < 100ms
- **Bottlenecks:** None

## Overall Pipeline Performance

**Typical Full Verification Run:**
- Small interface (5 functions, 20 constraints): 10-30 seconds
- Medium interface (20 functions, 80 constraints): 1-3 minutes
- Large interface (100 functions, 400 constraints): 5-15 minutes

**Breakdown by Phase (Medium Interface):**
- Ingestion: 5%
- Normalization: 2%
- Synthesis: 5%
- Versioning: 1%
- Adapter Generation: 3%
- Test Generation: 5%
- Execution: 70%  ← Dominant phase
- Monitoring Overhead: 5%
- Diagnostics: 2%
- Reporting: 2%

## Scalability Limits

### Theoretical Limits:
- **Maximum Functions:** ~10,000 (limited by Python memory, not design)
- **Maximum Constraints:** ~100,000 (limited by JSON serialization performance)
- **Maximum Test Cases:** ~100,000 (limited by execution time, not design)

### Practical Limits (for reasonable execution time):
- **Recommended Functions:** < 100
- **Recommended Constraints:** < 1,000
- **Recommended Test Cases:** < 1,000 (translates to < 5min execution)

## Memory Usage

**Typical Memory Footprint:**
- Orchestration: < 50 MB
- Ingestion: 100-500 MB (libclang)
- Normalization: 50-200 MB
- Synthesis: 50-200 MB
- Execution: 100-500 MB per subprocess
- Reporting: 50-200 MB

**Peak Memory:** ~1-2 GB for large interfaces

## Performance Optimization Recommendations

### For Users:
1. **Cache Artifacts:** Reuse contract.json across runs if interface hasn't changed
2. **Selective Verification:** Verify only changed functions (requires manual test plan filtering)
3. **Parallel Execution:** Run multiple verifier instances for different headers (manual orchestration)
4. **Reduce Test Count:** Use sampling for large interfaces (trade coverage for speed)

### For Future Development:
1. **Parallel Test Execution:** Run multiple subprocesses concurrently ( improvement)
2. **Incremental Verification:** Only re-verify changed functions
3. **Lazy Loading:** Load artifacts on-demand rather than upfront
4. **Caching:** Cache expensive computations (e.g., typedef resolution)

## Performance Monitoring

The system does not currently include built-in performance profiling.

**Manual Profiling:**
```python
python -m cProfile -o profile.stats polyglot_ffi_verifier.py verify ...
python -m pstats profile.stats
```

### Recommended Metrics:
- Time per phase (currently logged to stdout)
- Memory usage per phase (use external tools)
- Test execution rate (tests/second)

## When Performance Matters
Performance is acceptable for:
- Development-time verification (interactive use)
- CI pipelines (< 5 minute builds)
- Pre-commit hooks (with small interfaces)

Performance is insufficient for:
- Runtime enforcement (use generated adapters, not full verification)
- High-frequency testing (e.g., every function call)
- Real-time verification
