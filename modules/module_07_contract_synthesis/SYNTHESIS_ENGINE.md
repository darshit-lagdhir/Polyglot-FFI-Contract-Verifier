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

## Advanced Constraint Generation (Prompt 2/15)

### Relational Constraints
Detects and encodes relationships between parameters, particularly buffer-length pairs.

**Detection Strategy:**
- Structural adjacency (pointer + integer parameter)
- Naming conventions (uffer + length)
- Type semantics (unsigned size types)
- Parameter ordering (standard vs reverse)

**Confidence Scoring:**
- >= 0.8: ERROR severity
- >= 0.6: WARNING severity
- >= 0.4: INFO severity
- < 0.4: No clause generated

### Calling Convention Constraints
Projects calling convention requirements from IR to contract.

**Supported Conventions:**
- cdecl (C default)
- stdcall (Windows API)
- astcall (register-based)
- ectorcall (SIMD)

### ABI Compatibility Constraints
Binds contract to specific compiled artifact fingerprints.

**Metadata Captured:**
- Symbol name hashes
- Layout fingerprints
- ABI version identifiers

### Updated Synthesis Phases
**Phase 3: Relational Constraint Derivation**
- Buffer-length pattern detection
- Confidence-based severity assignment

**Phase 4: Calling Convention Constraints**
- Convention projection from IR
- Platform-specific handling

**Phase 5: ABI Compatibility Constraints**
- Fingerprint binding
- Version tracking

## Contextual Intelligence (Prompt 3/15)
### Contextual Analyzer
Performs interface-wide analysis to detect patterns and strengthen synthesis.

**Analysis Capabilities:**
- Cross-function pattern detection
- Naming convention consistency
- Ownership symmetry detection (create/destroy pairs)
- Interface coherence scoring
- Anomaly detection

**Pattern Strength Metric:**

`python
pattern_strength = (occurrences / total_functions) * consistency_score
``n
### Conditional Refinement
Generates clauses with conditional semantics:

**Conditional Nullability:**
- If length > 0, buffer must be non-null`n- If length == 0, buffer may be null`n
**Benefits:**
- More precise than absolute constraints
- Captures common C idioms
- Reduces false positives

### Severity Escalation
Escalates clause severity based on contextual evidence:

**Escalation Rules:**
- Pattern repetition (3+ occurrences)  increase severity
- Ownership symmetry detected  escalate ownership clauses
- Interface-wide consistency  strengthen constraints

**Limits:**
- Maximum one level increase
- Never escalate INFO directly to ERROR
- Requires 0.8+ confidence

### Advisory Clauses
Non-fatal clauses for ambiguous situations:

**Advisory Types:**
- Pattern ambiguity (insufficient confidence)
- Interface inconsistency (deviation from pattern)
- Ownership uncertainty (unclear transfer semantics)

**Purpose:** Guide manual refinement and document uncertainties
