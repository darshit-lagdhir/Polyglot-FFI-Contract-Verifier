# Logging Strategy

## Overview
Standardized logging is crucial for diagnosing verification issues, understanding execution flow, and debugging integration problems. This document defines the logging strategy for the Polyglot FFI Contract Verifier.

## Logging Levels

The system uses standard Python logging levels with specific semantic meanings:

| Level | Usage | Target Audience | Example |
|-------|-------|-----------------|---------|
| `CRITICAL` | System cannot continue. Immediate exit. | User | "Disk full - cannot write report" |
| `ERROR` | Operation failed, but pipeline might proceed. | User | "Failed to parse header file" |
| `WARNING` | Something looks wrong, but using defaults. | User | "Function 'foo' has no constraints" |
| `INFO` | High-level progress steps. | User | ": Ingestion complete" |
| `DEBUG` | Detailed execution logic. | Developer | "Parsed AST node: FunctionDecl" |

## Log Output Channels

### 1. Console (Standard Output/Error)
- **Content**: `INFO` and higher.
- **Format**: Human-readable, minimal metadata.
- **Purpose**: Interactive feedback for the user.

**Format:**
```text
[INFO] Verifying contract...
[WARN] Constraint 'len' references non-existent param 'n'
```

### 2. Execution Log (`execution_log.json`)
- **Content**: Structured data about test execution.
- **Format**: JSON.
- **Purpose**: Machine-readable record of functional verification.
- **Persistence**: Persisted to `artifacts/execution_log.json`.

### 3. Debug Log (`debug_output.txt`)
- **Content**: `DEBUG` and higher.
- **Format**: Full timestamped log lines with module names.
- **Purpose**: Diagnostics internal logic and tracing flow.
- **Persistence**: Temporary file in working directory (optional).

## Contextual Logging

Logs are enriched with context where possible to aid debugging:

- **Execution ID**: Unique UUID for the run (traceable across system).
- **Phase Name**: All logs indicate the active pipeline phase.
- **Component**: The specific module generating the log.

## Best Practices for Developers

1.  **Do not log secrets**: Never log environment variables that might contain keys.
2.  **Use lazy formatting**: Use `logger.debug("Val: %s", val)` instead of f-strings for performance.
3.  **Log boundaries**: Log entry and exit of major phases.
4.  **Structured info**: When logging about a function or constraint, include its ID.

## Log Parsing for Automation

Do not rely on parsing console output for automation. Use the structured artifacts instead:
- **Status Checks**: Parse `ci_summary.json`.
- **Test Results**: Parse `execution_log.json`.
- **Diagnostics**: Parse `diagnostics.json`.

Console output format is subject to change for UX improvements.
