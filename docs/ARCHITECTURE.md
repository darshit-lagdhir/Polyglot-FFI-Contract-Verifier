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
<!-- File Integrity Identifier: c9622ac80d99a24a -->
<!-- ============================================================================== -->

# Language Adapter Architecture

## Overview

The Language Adapter is a runtime FFI enforcement system that validates
foreign function calls against contracts, manages memory ownership, and
provides comprehensive observability.

## System Architecture

### Layer 1: Core Validation

**Components:**
- `ValidationEngine`: Executes validation rules
- `ValidationGraph`: Dependency graph of validation clauses
- `PredicateFactory`: Creates validation predicates

**Flow:**
Input → Normalization → Validation Graph → Predicates → Result

### Layer 2: Invocation Pipeline

**Components:**
- `InvocationOrchestrator`: Coordinates invocation phases
- `NormalizationInterface`: Converts values to canonical form
- `CrashIsolationBoundary`: Handles native crashes

**Phases:**
1. Pre-validation
2. Native invocation
3. Post-validation
4. Cleanup

### Layer 3: Memory & Ownership

**Components:**
- `OwnershipGraph`: Tracks memory ownership
- `PythonMemoryManager`: Manages Python FFI memory
- `TransferSemantics`: Implements ownership transfers

**Tracking:**
- Allocation tracking
- Ownership state machine
- Transfer annotations
- Lifecycle hooks

### Layer 4: Observability

**Components:**
- `StructuredLogger`: Context-aware logging
- `MetricsCollector`: Performance metrics
- `TracingContext`: Distributed tracing
- `EventEmitter`: Real-time events

## Data Flow

User Code
↓
Public API (`create_adapter`, `call_with_enforcement`)
↓
`LanguageAdapter`
↓
`InvocationOrchestrator`
↓
┌─────────────┬──────────────┬─────────────┐
│ Validation  │ Invocation   │ Cleanup     │
│ Engine      │ Pipeline     │ Manager     │
└─────────────┴──────────────┴─────────────┘
↓             ↓              ↓
┌─────────────┬──────────────┬─────────────┐
│ Contract    │ Memory       │ State       │
│ Clauses     │ Management   │ Tracking    │
└─────────────┴──────────────┴─────────────┘

## Extension Points

1. **Custom Validators**: Implement `ValidationInterface`
2. **Custom Normalizers**: Implement `NormalizationInterface`
3. **Custom Policies**: Create `EnforcementPolicy`
4. **Custom Metrics**: Subscribe to `EventEmitter`