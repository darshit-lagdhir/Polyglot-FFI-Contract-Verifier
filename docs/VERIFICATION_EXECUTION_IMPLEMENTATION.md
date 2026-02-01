# Verification Execution Implementation

This document details the implementation of **: Verification Execution** for the Polyglot FFI Contract Verifier.

## Overview

The Verification Execution Engine is the active component that runs contract tests. It consumes declarative test plans (), invokes contract-enforcing adapters (), and produces an immutable execution log.

## Execution Algorithm

The engine follows a 6-step loop for each test case:

1.  **Test Case Initialization**: Load metadata, category, and expected outcomes from the plan.
2.  **Input Instantiation**: Convert JSON-based values into `ctypes` primitives, structs, and pointers.
3.  **Adapter Invocation**: Dynamically load the generated Python adapter and call the specified function.
4.  **Exception Classification**: Catch all exceptions. Map known contract violations (from ) to specific results.
5.  **Outcome Validation**: Compare the actual result (success or exception) against the expected one.
6.  **Immutable Logging**: Record results, timing, and failure reasons in the append-only log.

## Input Instantiation

The `InputInstantiator` bridges the gap between the portable test plan and Python's memory model:
- **Primitives**: Direct mapping to `ctypes.c_*` types.
- **Pointers**: Handles `NULL` as `None` or casts memory to the appropriate pointer type.
- **Structs**: Recursively instantiates fields using the generated `_structs.py` module.
- **Buffers**: Allocates memory and populates it with test data.

## Outcome Assessment

Tests are classified into three logical results:
- **PASS**: Actual outcome matches expectations (e.g., a negative test correctly triggered a violation).
- **FAIL**: Mismatch (e.g., a function succeeded when it should have failed, or vice-versa).
- **ERROR/CRASH**: Unexpected infrastructure failure or native library crash.

## Isolation and Reproducibility

- **Test Isolation**: Each test is independent. A crash or failure in one test does not propagate state to the next.
- **Determinism**: By using fixed inputs from the test plan, the execution results are reproducible across identical library versions.

## Artifacts

1.  **`execution_log.json`**: The complete audit trail of the verification run.
2.  **`execution_summary.txt`**: A human-readable report summarizing pass rates and critical failures.
