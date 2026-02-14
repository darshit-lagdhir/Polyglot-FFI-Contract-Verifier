# Module 07: Contract Synthesis Engine

## Overview

The Contract Synthesis Engine transforms structural facts encoded in Module 05 IR artifacts into explicit semantic assumptions expressed as Module 06 Contract documents. It implements a deterministic, conservative, and traceable semantic projection layer.

## Purpose

- **Input**: IR Interface Unit (structural compiler truth)
- **Output**: Contract Document (enforceable runtime expectations)
- **Transformation**: Deterministic semantic projection with complete traceability

## Key Components

### SynthesisEngine
Main orchestrator coordinating all synthesis phases.

### LayoutClauseGenerator
Generates layout clauses encoding structural invariants for:
- Structures (size, alignment, field offsets, padding)
- Unions (overlapping members, max size)
- Scalars (bit width, signedness)

### NullabilityClauseGenerator
Generates nullability clauses for pointer parameters.
- Default: non-null (conservative)
- Detects nullable signals in parameter names

### OwnershipClauseGenerator
Generates ownership clauses for return values.
- Default: caller-owned (conservative)
- Advisory severity (requires manual review)

## Synthesis Phases

1.  **Phase 1: Structural Invariant Projection**
    - Layout clauses for all types
    - Scalar property clauses

2.  **Phase 2: Pointer Assumption Projection**
    - Nullability clauses for pointer parameters
    - Mutability clauses for const pointers
    - Ownership clauses for return values

## Configuration

Synthesis behavior controlled via `SynthesisConfig`:
- `synthesis_version`: Version identifier
- `default_pointer_nonnull`: Nullability default
- `default_return_ownership`: Ownership default
- Generator toggles (enable/disable clause types)

## Provenance Tracking

Every clause includes provenance metadata:
- IR entity that triggered generation
- Synthesis rule identifier and version
- Triggering structural properties
- Confidence level
- Human-readable explanation

## Guarantees

- **Determinism**: Identical input → identical output
- **Conservative Safety**: Strict defaults unless proven otherwise
- **Complete Traceability**: Every clause explains its origin
- **Schema Compliance**: All output validates against Module 06 schema

## Usage

```python
from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig

# Configure synthesis
config = SynthesisConfig(
    synthesis_version="1.0.0",
    default_pointer_nonnull=True
)

# Create engine
engine = SynthesisEngine(config)

# Synthesize contract from IR
result = engine.synthesize(ir_unit, "my_interface")

if result.success:
    contract = result.contract
    print(f"Generated {result.clauses_generated} clauses")
else:
    print("Errors:", result.errors)
```

## Integration

- **Input**: `IRInterfaceUnit` from Module 05
- **Output**: `ContractDocument` for Module 06
- **Bridge**: Direct API integration (no serialization needed)
