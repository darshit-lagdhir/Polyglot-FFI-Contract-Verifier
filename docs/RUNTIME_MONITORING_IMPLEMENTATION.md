# Runtime Monitoring Implementation

This document details the implementation of **: Runtime Monitoring and Crash Detection** for the Polyglot FFI Contract Verifier.

## Overview

Runtime Monitoring ensures that native crashes (segfaults, access violations, etc.) are detected and recorded even when they bypass standard Python exception handling. This is achieved by executing each test case in an isolated subprocess.

## Architecture

The system uses a parent-child process model:
- **Parent Process**: Orchestrates the verification run, spawns children, and monitors their exit status.
- **Child Process**: Executes exactly one test case using the generated adapters.
- **IPC**: Results are serialized to JSON and communicated via stdout.

## Crash Detection Mechanism

### Subprocess Monitoring
The parent process uses the subprocess return code to detect abnormal termination:
- **Windows**: Detects NT status codes like `0xC0000005` (Access Violation).
- **Linux**: Detects signals like `SIGSEGV` (Segmentation Fault) or `SIGABRT` (Abort).

### Heuristic Analysis
`CrashAnalyzer` uses heuristics to classify crashes:
- Addresses near `0x0` are classified as **Null Pointer Dereferences**.
- Crashes during tests with `BufferSizeViolation` expectations are flagged as **Buffer Overflows**.

## Classification of Failures

1.  **SUCCESS**: Test returned exact expected value or raised expected exception.
2.  **FAILURE**: Test returned wrong value or wrong exception.
3.  **CRASH**: Native code terminated the process (e.g., Segfault).
4.  **TIMEOUT**: Test exceeded the allowed duration (default 60s).

## Artifacts

### Execution Log Augmentation
The `execution_log.json` is enhanced with a `crash_info` block for crashed tests:
```json
{
  "test_id": "test_001",
  "status": "failed",
  "crash_detected": true,
  "crash_info": {
    "crash_type": "access_violation",
    "exit_code": -1073741819
  }
}
```

### Crash Reports
For every crash, a detailed report is saved in `artifacts/crashes/crash_<test_id>_<timestamp>.json` containing context and analysis.

## Platform Support
- **Windows**: Supports SEH-based exit code detection.
- **Linux**: Supports signal-based termination detection.
