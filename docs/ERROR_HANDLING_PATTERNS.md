# Error Handling Patterns

## Overview
This document outlines the standardized error handling strategy used across the Polyglot FFI Contract Verifier. A consistent approach to error management ensures that failures are classified correctly, actionable feedback is provided to the user, and the system fails gracefully without undefined behavior.

## Error Taxonomy

The system explicitly distinguishes between three categories of errors:

### 1. User Errors (Input Validation)
Errors caused by invalid input, misconfiguration, or missing files. These are expected and should be reported with clear instructions for resolution.
- **Examples**: Missing header file, invalid JSON schema, unsupported compiler version.
- **Handling**: Catch specific exceptions, print friendly error message, exit with code `1`.
- **Traceback**: Suppressed by default (unless `--debug` is used).

### 2. System Errors (Infrastructure)
Errors caused by environmental issues, resource exhaustion, or external dependency failures.
- **Examples**: libclang crash, out of memory, file permission denied, native library load failure.
- **Handling**: Catch specific exceptions, suggest environmental fixes, exit with code `2`.
- **Traceback**: Logged to debug file.

### 3. Internal Errors (Bugs)
Unexpected states or logic errors within the verifier itself.
- **Examples**: Assertion failure, key error in internal dict, unhandled type.
- **Handling**: Catch generic `Exception` at top level, print "Internal Error" banner, exit with code `3`.
- **Traceback**: Always printed to facilitate bug reporting.

## Exception Hierarchy

All custom exceptions inherit from `PolyglotFFIError`.

```python
class PolyglotFFIError(Exception):
    """Base class for all verifier exceptions."""

class ConfigError(PolyglotFFIError):
    """Invalid user configuration."""

class IngestionError(PolyglotFFIError):
    """Failures during native interface parsing."""

class SynthesisError(PolyglotFFIError):
    """Failures during contract synthesis."""

class VerificationError(PolyglotFFIError):
    """Failures during test execution (not test failures)."""
```

## Exit Codes

The CLI uses standard exit codes to communicate status to automation tools:

| Code | Meaning |
|------|---------|
| `0`  | Success (Verification Passed) |
| `1`  | Verification Failed (Contract Violations Found) |
| `2`  | User/Config Error |
| `3`  | System/Environment Error |
| `4`  | Internal Error |

## Recovery Strategies

### 1. Verification Failures
If a verification test fails (e.g., native code crash):
- **Action**: The `MonitoredVerificationExecutor` catches the subprocess exit code.
- **Recovery**: Log the failure as a `Critical Violation` and continue to the next test.
- **Result**: The pipeline completes, but the final report status is "FAILED".

### 2. Partial Results
If the pipeline crashes mid-execution:
- **Action**: Artifacts from completed phases are persisted on disk.
- **Recovery**: User can inspect `execution_log.json` to see how far it got.
- **Restart**: Re-running the command overwrites previous artifacts safely.

## User Messaging Guidelines

Error messages should follow the **"What, Why, Fix"** pattern:

1.  **What happened**: "Could not load native library."
2.  **Why it happened**: "File 'build/lib.dll' not found."
3.  **How to fix it**: "Ensure the build path is correct and the library is compiled."

**Bad Example:**
`FileNotFoundError: [Errno 2] No such file or directory: 'lib.dll'`

**Good Example:**
`Error: Native library not found at 'lib.dll'. Please check the --library-path argument.`

## Implementation in Code

Global exception handler pattern in `polyglot_ffi_verifier.py`:

```python
def main():
    try:
        # Run pipeline
        orchestrator.run()
    except PolyglotFFIError as e:
        print(f"❌ Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"💥 Internal Error: {e}")
        traceback.print_exc()
        sys.exit(4)
```
