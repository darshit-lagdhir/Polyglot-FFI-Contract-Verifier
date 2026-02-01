# Diagnostics Mapping and Failure Classification Implementation

This document details the implementation of **0: Diagnostics Mapping** for the Polyglot FFI Contract Verifier.

## Overview

Diagnostics Mapping transforms raw execution results (test outcomes and native crashes) into human-understandable, semantic insights. It bridges the gap between technical symptoms (e.g., "Access Violation at 0x0") and contract violations (e.g., "Missing null check for parameter 'cfg'").

## Failure Classification

The `FailureClassifier` uses a decision tree to categorize failures:

1.  **Failure Mode Detection**:
    - `passed`: Not a failure.
    - `crashed`: Native process termination (Segfault, Access Violation).
    - `failed`: Python-level failure (wrong return value, missing exception).
    - `timeout`: Native code hung.

2.  **Severity Assignment**:
    - **CRITICAL**: Buffer overflows, use-after-free, and any native crash.
    - **HIGH**: Missing null pointer enforcement.
    - **MEDIUM**: Type layout mismatches or custom constraint violations.
    - **LOW**: Minor discrepancies or informational issues.

## Root Cause Analysis

The `RootCauseAnalyzer` identifies four primary failure patterns:

- **Adapter Missing Enforcement**: Native crash occurred because the adapter didn't reject invalid input.
- **Adapter Missing Pre-call Check**: Test expected an exception but native code was called without validation.
- **Unexpected Exception Type**: Adapter raised an exception, but not the specific one required by the contract.
- **Native Deadlock**: Native code timed out.

## Remediation Generation

The `RemediationGenerator` produces actionable instructions including:
- Concrete code snippets for pre-call checks.
- Specific adapter files and functions requiring modification.
- Contract revision suggestions if the specification is insufficient.

## Violation Aggregation

To avoid "alert fatigue," the `ViolationAggregator` groups related test failures by the underlying **Constraint ID**. Even if 100 tests fail due to a single missing null check, they are reported as one aggregated violation with a "Affected Tests" count.

## Artifacts

### `diagnostics.json`
Machine-readable report containing:
- Summary statistics (passed/total, severity counts).
- Aggregated violations with full context (impact, cause, fix).
- Provenance metadata for traceability.

### `violation_summary.txt`
Human-readable executive summary listing critical and high-severity issues first with clear remediation steps.

## Usage

Run the diagnostics stage independently:
```bash
python polyglot-ffi-verifier.py diagnose
```
Or as part of the full pipeline:
```bash
python polyglot-ffi-verifier.py verify <header> <library>
```
