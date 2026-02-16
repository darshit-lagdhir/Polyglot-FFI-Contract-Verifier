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

## Bridge Integration (Prompt 4/15)

The synthesis engine now utilizes explicit bridge layers to ensure robust integration with Module 05 (IR) and Module 06 (Contract Schema).

### Architecture

The integration follows a 3-layer architecture:

1.  **IR Bridge (Module 05 -> Module 07)**:
    -   Consumes strictly typed `IRInterfaceUnit` artifacts.
    -   Performs rigorous validation of IR completeness, type consistency, and coherence.
    -   Normalizes input for the synthesis core.
    -   Supports strict (fail-fast) and loose (warn-only) validation modes.

2.  **Synthesis Core (Module 07)**:
    -   The central logic engine (unchanged in purpose, but now isolated).
    -   Operating on validated IR entities.
    -   Generating raw `ContractClause` objects in memory.

3.  **Contract Bridge (Module 07 -> Module 06)**:
    -   Consumes raw generated clauses.
    -   Validates each clause against Module 06 schema definitions.
    -   Assembles the final `ContractDocument` with deterministic ordering.
    -   Injects synthesis metadata and provenance information.

### Validations

**IR Validation Rules (`IRValidator`):**
-   **Type Completeness**: All referenced types must be defined.
-   **Signature Coherence**: Function signatures must have valid return types and parameters.
-   **ABI Metadata**: Target architecture and pointer width must be specified.

**Contract Validation Rules (`ContractSchemaValidator`):**
-   **Structure**: Clauses must have IDs, types, and subject references.
-   **Schema Compliance**: Must satisfiy Module 06 validation logic (e.g., valid fields).
-   **Determinism**: Output clause order is stable (sorted by type and ID).

### Expanded Workflow

The `synthesize` method now orchestrates the following pipeline:

1.  **Phase -1**: IR consumption and validation via `IRBridge`.
2.  **Phase 0**: Contextual Analysis.
3.  **Phase 1-5**: Clause Generation (Layout, Nullability, Ownership, Relational, CLI, ABI).
4.  **Phase 6**: Severity Escalation.
5.  **Phase 7**: Advisory Generation.
6.  **Phase 8**: Contract Assembly and final validation via `ContractBridge`.

This architecture ensures that the synthesis engine is resilient to malformed inputs and guarantees that its outputs are always schema-compliant contracts ready for enforcement.

## Synthesis Versioning (Prompt 5/15)

### Version Management

Synthesis versions follow semantic versioning:

-   **MAJOR**: Breaking changes to rule semantics (requires contract regeneration)
-   **MINOR**: New rules added (backward compatible)
-   **PATCH**: Bug fixes, no semantic changes

### Rule Registry

All synthesis rules are registered with immutable IDs.

Rule Properties:
-   `rule_id`: Immutable identifier
-   `rule_version`: Semantic version
-   `category`: Rule category (e.g., layout, nullability)
-   `introduced_in_synthesis`: When rule was added
-   `deprecated_in_synthesis`: When rule was deprecated (if applicable)

### Fingerprinting

Synthesis operations generate cryptographic fingerprints for:
-   **IR Fingerprint**: Input correctness
-   **Ruleset Fingerprint**: Active rule configuration
-   **Config Fingerprint**: Synthesis settings
-   **Output Fingerprint**: Generated contract content
-   **Composite Hash**: Overall operation signature

### Regression Detection

Baseline fingerprints enable automatic regression detection:
1.  Record baseline for reference IR artifacts.
2.  On subsequent synthesis, compare fingerprints.
3.  Detect version changes (INFO) or determinism violations (ERROR).

### Determinism Verification

Verify synthesis produces identical output:
1.  Run synthesis multiple times on same input.
2.  Compare output fingerprints.
3.  Ensure all fingerprints match identically.

## Installation & Usage (Prompt 7/15)

### Installation

Install from PyPI:
```bash
pip install module-07-contract-synthesis
```

Install with development dependencies:
```bash
pip install module-07-contract-synthesis[dev]
```

### Quick Start

#### As Library
```python
from module_07_contract_synthesis import synthesize_from_ir

# Simple synthesis
contract = synthesize_from_ir('interface.json')
print(f"Generated {len(contract.clauses)} clauses")

# With custom configuration
from module_07_contract_synthesis import SynthesisConfig

config = SynthesisConfig(
    synthesis_version='1.0.0',
    strict_mode=True
)
contract = synthesize_from_ir('interface.json', config=config)
```

#### As CLI
```bash
# Synthesize contract
pfcv-synth synthesize input.json -o contract.json

# Validate contract
pfcv-synth validate contract.json

# Batch processing
pfcv-synth batch "interfaces/*.json" --output-dir contracts/

# Check determinism
pfcv-synth verify-determinism input.json
```

### Public API

Core classes:
- **SynthesisEngine**: Main synthesis orchestrator.
- **SynthesisConfig**: Configuration management.
- **SynthesisResult**: Synthesis operation result.

Convenience functions:
- `synthesize_from_ir(ir_path, config=None)`: Synthesize from file.
- `synthesize_from_file(ir_path, output_path, format)`: Synthesize and write.
- `validate_contract(contract_path)`: Validate contract.

Versioning:
- **RuleRegistry**: Rule tracking.
- `version_compare(v1, op, v2)`: Version comparison.
- **DeterminismVerifier**: Determinism checking.

### Type Hints

Full type hint support:
```python
from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
from module_05_ir_normalization.ir_entities import InterfaceUnit

config: SynthesisConfig = SynthesisConfig()
engine: SynthesisEngine = SynthesisEngine(config)
# result = engine.synthesize(ir_unit, "interface")
```

## Performance Optimization (Prompt 8/15)

### Caching System

Multi-level caching for synthesis operations:

- **L1**: Complete synthesis results (keyed by IR fingerprint)
- **L2**: Contextual analysis results
- **L3**: Per-rule execution results (keyed by rule ID and entity fingerprint)

Usage:
```python
from module_07_contract_synthesis.performance import SynthesisCache

cache = SynthesisCache(max_size=100)

# Check cache
result = cache.get_synthesis_result(ir_fingerprint, synthesis_version)
if result:
    return result  # Cache hit!

# Cache miss, perform synthesis
result = engine.synthesize(ir_unit, interface_id)

# Store in cache
cache.put_synthesis_result(ir_fingerprint, synthesis_version, result)
```

### Profiling Tools

Profile synthesis performance at phase and rule levels:

```python
from module_07_contract_synthesis.performance import PhaseProfiler, RuleProfiler

# Phase-level profiling
p_profiler = PhaseProfiler()
with p_profiler.profile_phase('layout_generation'):
    generate_layout_clauses()

print(p_profiler.get_report())

# Rule-level profiling
r_profiler = RuleProfiler()
r_profiler.record_execution('nullability_rule', 0.045)
print(r_profiler.get_report())
```

### Benchmarking

Run performance benchmarks across different interface sizes:

```python
from module_07_contract_synthesis.performance import SynthesisBenchmark

benchmark = SynthesisBenchmark(engine)
result = benchmark.run_benchmark('medium', iterations=10)

print(f"Avg time: {result.avg_time_ms:.2f}ms")
print(f"Passed: {result.passed}")
```

### Performance Targets

- **Tiny** (5 functions): < 50ms
- **Small** (20 functions): < 100ms
- **Medium** (100 functions): < 500ms
- **Large** (500 functions): < 2000ms

## Module Completion & Validation (Prompt 9/15)

### Completeness Validation

The synthesis module includes an automated completeness validator that checks core features, integration, tooling, documentation, and API stability.

```python
from module_07_contract_synthesis.completion_check import CompletenessValidator

validator = CompletenessValidator()
report = validator.validate_completeness()

print(report.get_summary())

if report.is_complete():
    print("Module is production-ready!")
```

### CLI Completion Check

You can run the completeness check directly from the command line:

```bash
python -m module_07_contract_synthesis.completion_check
```

Example Output:
```text
Module 07: Contract Synthesis Engine
Completeness Validation Report
======================================================================

Core Features: 6/6 (100%)
  ✓ Layout clause generation
  ✓ Nullability clause generation
  ✓ Ownership clause generation
  ✓ Relational constraint derivation
  ✓ Calling convention projection
  ✓ ABI compatibility clauses

Advanced Features: 4/4 (100%)
  ✓ Contextual analysis
  ✓ Conditional refinement
  ✓ Severity escalation
  ✓ Advisory clause generation

Integration: 2/2 (100%)
  ✓ IR Bridge
  ✓ Contract Bridge

Tooling: 3/3 (100%)
  ✓ CLI interface
  ✓ Versioning system
  ✓ Performance optimization

Documentation: 2/2 (100%)
  ✓ SYNTHESIS_ENGINE.md
  ✓ Package docstring

Public API: 3/3 (100%)
  ✓ __all__ export list
  ✓ Core classes importable
  ✓ Convenience functions importable

======================================================================
Total: 20/20 checks passed

Status: ✓ MODULE COMPLETE AND READY
```

### Integration Testing

The module includes a comprehensive integration test suite that verifies the full pipeline from IR Normalization (Module 05) through Contract Schema (Module 06).

Run integration tests:
```bash
pytest tests/unit/test_synthesis_completion.py -v
```

## Examples & Tutorials (Prompt 10/15)

The synthesis module provides extensive learning resources to help you get started quickly and follow best practices.

### Quick Start (5 Minutes)

```python
from module_07_contract_synthesis import synthesize_from_ir

# Single function call to generate highly-detailed FFI contracts
contract = synthesize_from_ir('my_interface.json')

print(f"Generated {len(contract.clauses)} enforcement clauses!")
```

### Tutorial Series

Follow our progressive tutorials to master the synthesis engine:

1. **[Tutorial 01: Your First Contract Synthesis](../../docs/tutorials/module_07_tutorial_01.md)** (Beginner, 10 min)
   - Setup, basic usage, and examining output.
2. **Tutorial 02: Advanced Configuration** (Intermediate, 15 min)
   - Customizing non-null signals, severity levels, and generators.
3. **Tutorial 03: Understanding Traceability** (Intermediate, 20 min)
   - Deep dive into Clause Provenance and Rule Registry.

### Example Gallery

Located in `examples/module_07/`:
- `01_simple_synthesis.py`: Basic workflow guide.
- `02_configuration.py`: Demonstration of various `SynthesisConfig` settings.
- `10_performance_optimization.py`: Usage of `SynthesisCache` and `PhaseProfiler`.

Run any example from the project root:
```bash
python examples/module_07/01_simple_synthesis.py
```

### Best Practices

- **✓ Pin Synthesis Versions**: Use explicit versions in `SynthesisConfig` for production stability.
- **✓ Monitor Performance**: Use the `PhaseProfiler` during development to identify interface complexity issues.
- **✓ Always Check Results**: Synthesis can succeed partially; always check `result.errors` and `result.warnings`.
- **✓ Leverage Provenance**: Use the generated metadata to explain *why* a constraint exists to end-users.

### Troubleshooting

If you encounter issues during synthesis, consult the **[Troubleshooting Guide](../../docs/TROUBLESHOOTING.md)** for solutions to common validation and performance problems.
