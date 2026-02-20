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
<!-- File Integrity Identifier: 239df7b4dbbea70c -->
<!-- ============================================================================== -->

# Architecture Deep Dive

This document provides a technical overview of the Verification Pipeline (Module 02) internal architecture.

## Design Philosophy

The pipeline is built on three core pillars:
1. **Determinism**: Identical inputs must yield identical artifacts.
2. **Explicitness**: Every assumption is encoded in a machine-readable JSON artifact.
3. **Isolation**: Stages communicate only through validated files, never shared memory.

## Core Components

### 1. `PipelineStage` (Abstract Base Class)
Every stage implements this interface:
- `validate_inputs()`: Checks pre-conditions.
- `execute()`: Performs the actual logic.
- `validate_outputs()`: Checks post-conditions (schema validation).

### 2. `CompletePipeline` (Orchestrator)
Orchestrates the 7 stages:
- Manages artifact flow between stages.
- Handles error propagation.
- Tracks execution metadata.

### 3. `CacheManager` (SQLite Backend)
Provides intelligent artifact caching:
- Hashes input artifacts to detect changes.
- Stores metadata in `cache.db`.
- Prevents redundant execution of expensive stages like header parsing.

### 4. `ParallelPipelineExecutor`
Implements level-based parallelism:
- Analyzes stage dependencies.
- Groups independent stages (e.g., Adapter Gen and Test Plan Gen).
- Executes groups concurrently using `ThreadPoolExecutor`.

## Stage Breakdown

### Stage 1: Native Interface Ingestion
- **Tool**: `libclang`
- **Output**: `native_interface.json`
- **Logic**: Parses C header AST, extracts functions, structs, and enums.

### Stage 2: IR Normalization
- **Output**: `ir.json`
- **Logic**: Resolves typedefs, canonicalizes type names, and flattens nested structures.

### Stage 3: Contract Synthesis
- **Output**: `contract.json`
- **Logic**: Applies heuristics (e.g., `_len` suffix matching) to infer safety constraints like buffer sizes.

### Stage 4: Adapter Generation
- **Output**: Python bridge (`ctypes` wrappers)
- **Logic**: Generates safety-hardened Python code that enforces `contract.json` at runtime.

### Stage 5: Test Plan Generation
- **Output**: `test_plan.json`
- **Logic**: Generates combinatorial test cases for valid and invalid inputs.

### Stage 6: Verification Execution
- **Output**: `execution_log.json`
- **Logic**: Runs generated tests against the library and captures results/violations.

### Stage 7: Diagnostics & Reporting
- **Output**: `report.html` & `diagnostics.json`
- **Logic**: Classifies failures as "Crashes", "Violations", or "False Positives".

## Extension Points

### Hooks
Registration of custom functions at lifecycle points:
- `PRE_STAGE`, `POST_STAGE`
- `PRE_PIPELINE`, `POST_PIPELINE`

### Plugins
Self-contained modules that register new rules or handlers.

---

**Next Steps**: See [Module 03 Integration Spec](MODULE_03_INTEGRATION_SPEC.md)