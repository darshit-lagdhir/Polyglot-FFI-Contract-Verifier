<!-- ============================================================================== -->
<!-- Polyglot FFI Contract Verifier -->
<!-- Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved. -->
<!--  -->
<!-- This file is part of the Polyglot FFI Contract Verifier ecosystem. -->
<!-- It is licensed under the Antigravity Source-Available and Technical  -->
<!-- Protection License (ASTPL). -->
<!--  -->
<!-- PROHIBITED USES: Commercial Use, Network Access Provision, and Machine  -->
<!-- Training Use are strictly prohibited absent explicit written authorization. -->
<!--  -->
<!-- Removal or alteration of this header may constitute a violation of the  -->
<!-- repository's governing agreements. -->
<!--  -->
<!-- File Integrity Identifier: 143b0e30d19fbc54 -->
<!-- ============================================================================== -->

# Language Adapter API Reference

## Overview

The Language Adapter provides runtime FFI enforcement for Python applications.
It interposes between foreign language runtimes and native code, validating
every cross-language invocation against explicit contract clauses.

## Core Classes

### PythonAdapterComplete

Main adapter class for Python FFI enforcement.

**Methods**:

- `load_contract(path)`: Load contract from file
- `call_with_enforcement(*args)`: Call function with enforcement
- `enable_caching()`: Enable result caching
- `help(topic)`: Get help for topic
- `get_statistics()`: Get adapter statistics
- `get_validation_graph(function_name)`: Get validation graph for function

### EnforcementScope

Context manager for resource-safe invocations.

**Usage**:

```python
with adapter.enforcement_scope('function_name') as scope:
    scope.add_buffer(buffer)
    result = scope.invoke(args)
```

### AdapterConfig

Configuration dataclass for the adapter.

**Fields**:

- `mode` (EnforcementMode): Enforcement mode (STRICT, ADVISORY, PERMISSIVE)
- `fail_fast` (bool): Whether to stop on first failure
- `enable_crash_isolation` (bool): Enable crash isolation
- `enable_ownership_tracking` (bool): Enable ownership tracking

## Enumerations

### EnforcementMode

- `STRICT`: All clauses treated as mandatory
- `ADVISORY`: Advisory clauses log warnings only
- `PERMISSIVE`: Continue execution on non-critical failures

### ClauseSeverity

- `MANDATORY`: Must be enforced
- `ADVISORY`: Warning only

### ValidationStatus

- `PENDING`: Not yet validated
- `PASSED`: Validation passed
- `FAILED`: Validation failed

## Validation System

### ValidationNode

Represents a single validation step in the validation graph.

### ValidationGraph

Directed graph of validation nodes for a function.

### ValidationEngine

Executes validation graphs against inputs.

## Ownership System

### OwnershipRegistry

Tracks pointer ownership across FFI boundaries.

### OwnershipState

Individual pointer ownership state.

### OwnershipKind

- `OWNED`: Caller owns the resource
- `BORROWED`: Caller has temporary access
- `FREED`: Resource has been freed

## Documentation System

### APIDocGenerator

Extracts API documentation from Python classes.

### ContractDocGenerator

Generates documentation from contract JSON artifacts.

### TutorialGenerator

Creates step-by-step tutorials from tagged examples.

### HelpSystem

Interactive help with topic-based lookup and partial matching.

### ReportFormatter

Formats performance, health, and configuration reports.

### DocumentationManager

Unified facade coordinating all documentation generators.

## Optimization System

### ValidationCache

LRU + TTL cache for validation results.

### PredicateCache

Cache for compiled predicate functions with hit-rate tracking.

### FastPathDetector

Identifies scenarios where full enforcement can be bypassed.

### LazyEvaluator

Defers expensive operations until results are needed.

### PerformanceProfiler

Per-operation timing with statistical aggregation.

### OptimizationManager

Unified facade for all optimization strategies.

## Introspection System

### ContractMetadata

Rich metadata including function-level info and versioning.

### StateSnapshot

Point-in-time capture of adapter state.

### HistoryTracker

Bounded history of invocations, violations, and state changes.

### QueryEngine

Dot-notation query interface for adapter state.

### MetadataEnricher

Enriches violation reports with contract metadata.

### IntrospectionAPI

High-level facade for runtime introspection.