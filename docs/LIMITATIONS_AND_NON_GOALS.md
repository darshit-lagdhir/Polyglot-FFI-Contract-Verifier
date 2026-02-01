# Limitations and Non-Goals

## Overview
This document explicitly states what the Polyglot FFI Contract Verifier does NOT do, known limitations, and deliberate non-goals. Understanding these boundaries is essential for setting appropriate expectations.

## Explicit Non-Goals

### 1. Functional Correctness of Native Code
**Not a Goal:** Verify that native functions implement correct business logic.

**Why:** The verifier checks FFI contract adherence (memory safety, calling conventions, ownership), not algorithmic correctness.

**Example:**
```c
// This function has correct FFI behavior but wrong logic
int add(int a, int b) {
    return a - b;  // Wrong! But FFI-safe.
}
```
The verifier will NOT detect this bug.

### 2. Static Analysis of Native Code
**Not a Goal:** Analyze native C/C++ implementation for bugs.

**Why:** The verifier tests runtime behavior via adapters, not source code analysis.

**Tools for static analysis:** Clang Static Analyzer, Coverity, PVS-Studio

### 3. Automatic Bug Fixing
**Not a Goal:** Automatically fix detected violations.

**Why:** Fixes require human judgment (fix adapter vs fix native code vs update contract).
The verifier provides recommendations, not automatic patches.

### 4. Runtime Production Enforcement
**Not a Goal:** Replace generated adapters in production with live verification.

**Why:** Full verification is too slow for production. Use generated adapters ( output) for runtime enforcement.

### 5. Cross-Language Semantic Verification
**Not a Goal:** Verify semantic equivalence between languages.
**Example:** Verify that Python binding semantics match C semantics.

**Why:** This requires formal verification, which is out of scope.

### 6. Performance Optimization of Native Code
**Not a Goal:** Suggest performance improvements for native code.

**Why:** Performance is orthogonal to correctness.

### 7. Memory Leak Detection (General)
**Not a Goal:** Detect all memory leaks in native code.

**Why:** Only ownership-transfer violations are detected. Internal leaks are not.
Use Valgrind or AddressSanitizer for comprehensive leak detection.

### 8. Concurrency Bug Detection
**Not a Goal:** Detect race conditions, deadlocks, or thread safety issues.

**Why:** Verification runs are single-threaded by design.

### 9. Binary Compatibility Verification
**Not a Goal:** Verify that compiled library matches header ABI.

**Why:** The verifier trusts that libclang reflects the compiled ABI. If compiler and header are mismatched, verification may pass incorrectly.

**Mitigation:** Use same compiler for both native library and ingestion.

## Known Limitations

### Platform Support
- **Supported:** Windows x64 (v1.0)
- **Not Supported:** Linux, macOS (future versions may add support)
- **Not Supported:** 32-bit architectures

### Language Support
- **Supported:** C interfaces
- **Partially Supported:** C++ (if interface is C-compatible with extern "C")
- **Not Supported:** C++ templates, classes, virtual functions

### Target Language Support
- **Supported:** Python adapters (v1.0)
- **Not Supported:** Rust, Go, JavaScript adapters (future versions may add support)

### Header Complexity
- **Supported:** Standard C headers
- **Limited Support:** Heavily templated headers (slow ingestion)
- **Not Supported:** Headers requiring C++ compiler (use extern "C" wrappers)

### Constraint Types
- **Supported:** Nullability, buffer sizes, struct layouts, ownership, calling conventions
- **Not Supported:** Alignment constraints beyond struct layout
- **Not Supported:** Endianness constraints
- **Not Supported:** Numeric range constraints (e.g., value must be 0-100)

### Test Coverage
- **Guaranteed:** 100% constraint coverage (every constraint tested)
- **Not Guaranteed:** 100% code path coverage in native library
- **Not Guaranteed:** All corner cases discovered

### Error Detection
- **Detects:** Contract violations, crashes, assertion failures
- **Does Not Detect:** Silent data corruption (unless it causes crash)
- **Does Not Detect:** Subtle undefined behavior (unless sanitizers enabled)

### Performance
- **Suitable For:** Development-time verification, CI pipelines
- **Not Suitable For:** Runtime production use, high-frequency testing

### Crash Detection
- **Detects:** Segfaults, access violations, illegal instructions, aborts
- **Does Not Detect:** Silent corruption, delayed crashes (after function returns)

### Ownership Tracking
- **Tracks:** Explicit ownership transfer (destroy functions, free functions)
- **Does Not Track:** Reference counting, shared ownership, custom allocators

## Edge Cases and Corner Cases

### 1. Platform-Specific Behavior
**Issue:** ABI details vary across platforms (calling conventions, struct padding).
**Limitation:** Verification on Windows does not guarantee correctness on Linux.
**Mitigation:** Run verification on target platform.

### 2. Compiler-Specific Behavior
**Issue:** Different compilers may have different padding, alignment, or calling conventions.
**Limitation:** Verification with MSVC does not guarantee correctness with GCC.
**Mitigation:** Use same compiler for verification and production.

### 3. Dynamic Linking Issues
**Issue:** Library may behave differently when statically vs dynamically linked.
**Limitation:** Verifier only tests dynamic linking (DLL/SO).

### 4. Callback Functions
**Issue:** Native code calling back into Python.
**Limitation:** Callbacks are not automatically verified (adapter does not wrap callbacks).
**Mitigation:** Manually test callback paths.

### 5. Variadic Functions
**Issue:** Functions with variable arguments (e.g., printf-style).
**Limitation:** Variadic functions are difficult to verify automatically.
**Status:** Limited support (tests only with fixed argument counts).

### 6. Function Pointers
**Issue:** Function pointers in structs or parameters.
**Limitation:** Function pointer validity cannot be verified automatically.
**Status:** Null checks only (no signature verification).

### 7. Opaque Pointers
**Issue:** Pointers to incomplete types (e.g., void* to internal struct).
**Limitation:** Cannot verify pointed-to data, only pointer nullability.

### 8. Const Correctness
**Issue:** Const qualifiers in C.
**Limitation:** Const is documented in contract but not enforced at runtime (Python/ctypes does not enforce const).

### 9. Global State
**Issue:** Native library may maintain global state.
**Limitation:** Tests are isolated but cannot detect state corruption across tests.

### 10. Timing-Dependent Bugs
**Issue:** Bugs that only manifest under specific timing (race conditions, timing attacks).
**Limitation:** Verification is deterministic and single-threaded.

## Workarounds and Alternatives

### For Functional Correctness:
- Use unit tests for native code
- Use property-based testing (e.g., Hypothesis)

### For Static Analysis:
- Use Clang Static Analyzer
- Use Coverity or PVS-Studio

### For Memory Safety:
- Compile native library with AddressSanitizer (ASan)
- Use Valgrind for leak detection

### For Concurrency:
- Use ThreadSanitizer (TSan)
- Use race detection tools

### For Performance:
- Use profiling tools (gprof, perf)
- Use benchmarking frameworks

## When NOT to Use This Tool

**❌ Do not use if:**
- You need functional correctness verification (use unit tests)
- You need static analysis (use Clang Static Analyzer)
- You need cross-platform verification (run on each platform)
- You need real-time enforcement (use generated adapters only)
- Your interface is C++ (use extern "C" wrappers first)

**✅ Use if:**
- You have C interfaces accessed from Python
- You want to detect FFI contract violations
- You want automated safety checks in CI
- You want actionable violation reports
