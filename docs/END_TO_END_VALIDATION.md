# End-to-End Validation Guide

This document explains how to validate the Polyglot FFI Contract Verifier system.

## Integration Tests

The integration test suite (`tests/integration/test_end_to_end.py`) does the following:

1.  Creates a temporary C interface (`test_interface.h`).
2.  Runs the **FULL PIPELINE** from ingestion to reporting.
3.  Mocks the native library execution (for portability) but validates all pipeline logic.
4.  Asserts that critical bugs are found and reported correcty.

### Running Integration Tests

```bash
python tests/integration/test_end_to_end.py
```

**Expected Output:**
```text
END-TO-END INTEGRATION TEST
...
✓ END-TO-END INTEGRATION TEST PASSED
```

## Demo

The demo (`examples/demo/`) is a user-friendly showcase.

### Running the Demo

```bash
python examples/demo/run_demo.py
```

The script simulates the verification of a vulnerable library, showing exactly what users encounter when the tool finds bugs.

## Diagnostics

### "Libclang analysis failed"
- If you see this warning in integration tests, it means `libclang` is not installed or configured.
- The test will fall back to using a mock interface to verify the rest of the pipeline.
- To fix: `pip install libclang` and ensure LLVM is installed.

### "Context setup failed"
- Ensure you are running from the project root or PYTHONPATH includes `src`.

## Validation Script

Run the all-in-one validation script to verify everything:

```bash
python validate_end_to_end_integration.py
```

This runs:
1. Integration Test
2. Demo Simulation
3. Regression Tests

## Regression Tests

Located in `tests/regression/`, these guard against:
- **Determinism**: Ensuring synthesis and generation produce identical outputs for identical inputs.
- **Consistency**: Ensuring artifact structures remain valid properly.

Run specifically:
```bash
python tests/regression/test_system_stability.py
```
