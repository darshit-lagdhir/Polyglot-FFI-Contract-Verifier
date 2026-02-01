# Test Plan Generation Implementation

This document details the implementation of **: Test Plan Generation** for the Polyglot FFI Contract Verifier.

## Overview

The Test Plan Generation subsystem transforms abstract FFI contracts () into comprehensive, structured test specifications (`test_plan.json`). It provides systematic, deterministic coverage of both valid use cases (positive tests) and error conditions (negative tests).

## Test Case Categories

The generator produces four primary categories of tests:

1.  **Positive Tests**: Valid inputs designed to satisfy all contract constraints. These verify that the native library and its adapter function correctly under normal conditions.
2.  **Negative Tests**: Deliberate constraint violations. For every `pre_condition` in the contract, a test case is generated that violates only that specific constraint. This verifies the enforcement logic in the  adapters.
3.  **Boundary Value Tests**: Edge cases for numeric parameters (e.g., `0`, `MAX_INT`, `MIN_INT`).
4.  **Ownership Tests**: (Future) Focused on monitoring memory lifecycle, such as double-free or use-after-transfer detection.

## Test Derivation Algorithm

1.  **Enumerate Constraints**: Every unique `constraint_id` is extracted from the contract.
2.  **Positive Case Generation**: For each function, "minimal" and "typical" success cases are generated.
3.  **Fault Injection**: For each constraint, an input set is created where only that constraint is violated.
4.  **Deterministic Values**: Inputs are generated using a seed-less, rule-based approach to ensure byte-identical test plans on every run.
5.  **Coverage Mapping**: Each test is linked back to the constraints it exercises.

## Input Generation Strategies

- **Primitives**: Uses a fixed set of boundary and typical values (e.g., `42` for `int32`).
- **Pointers**: Generates `null` for negative tests and valid buffers/structs for positive tests.
- **Structs**: Recursively populates fields using the IR type definitions.
- **Strings**: Ensures null-termination unless deliberately testing for its absence.

## Coverage Analysis

The system generates a `test_coverage.json` report summarizing:
- Total number of constraints.
- Percentage of constraints covered by at least one negative test.
- List of any uncovered constraints (e.g., those currently too complex for automated fault injection).

## Artifacts

1.  **`test_plan.json`**: The declarative test suite specification.
2.  **`test_coverage.json`**: Coverage analytics and mapping.
