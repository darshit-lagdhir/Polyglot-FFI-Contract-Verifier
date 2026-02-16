# API Reference: Module 07 Contract Synthesis Engine

Complete reference for all public APIs of the Polyglot FFI Contract Synthesis Engine.

## Core Functions

### synthesize_from_ir

```python
def synthesize_from_ir(
    ir_path: Union[str, Path],
    config: Optional[SynthesisConfig] = None,
    strict: bool = True
) -> ContractDocument
```

Synthesize a contract from an Intermediate Representation (IR) file. This is the primary high-level entry point for most users.

- **Parameters:**
    - `ir_path`: Path to an IR JSON file (string or `pathlib.Path`).
    - `config`: Optional `SynthesisConfig` instance. If `None`, default settings are used.
    - `strict`: If `True` (default), the function raises an exception on IR validation or contract assembly errors.
- **Returns:** A `ContractDocument` instance containing the generated clauses and metadata.
- **Raises:**
    - `FileNotFoundError`: If the input IR file does not exist.
    - `IRBridgeError`: If IR validation fails (in strict mode).
    - `ContractBridgeError`: If the synthesized contract fails schema validation.
    - `RuntimeError`: If synthesis fails due to structural errors.

---

### synthesize_from_file

```python
def synthesize_from_file(
    ir_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    format: str = 'json',
    config: Optional[SynthesisConfig] = None
) -> ContractDocument
```

Synthesize a contract and optionally save it to a file. Supports both JSON and YAML output formats.

- **Parameters:**
    - `ir_path`: Path to the input IR JSON file.
    - `output_path`: Optional path where the resulting contract should be saved.
    - `format`: Serialization format (`'json'` or `'yaml'`). Defaults to `'json'`.
    - `config`: Optional `SynthesisConfig` instance.
- **Returns:** The synthesized `ContractDocument`.

---

### validate_contract

```python
def validate_contract(contract_path: Union[str, Path]) -> bool
```

Validate an existing contract file against the Module 06 schema.

- **Parameters:**
    - `contract_path`: Path to a contract JSON file.
- **Returns:** `True` if valid.
- **Raises:** `RuntimeError` with validation details if the contract is invalid.

---

## Core Classes

### SynthesisEngine

The main orchestrator responsible for the multi-phase synthesis process.

```python
class SynthesisEngine:
    def __init__(self, config: Optional[SynthesisConfig] = None)
```

- **Methods:**
    - `synthesize(ir_unit: InterfaceUnit, target_interface_id: str) -> SynthesisResult`:
      Performs the actual synthesis operation on an in-memory `InterfaceUnit`.

---

### SynthesisConfig

Configuration container for controlling synthesis heuristics and generator behavior.

```python
@dataclass
class SynthesisConfig:
    synthesis_version: str = '1.0.0'
    default_pointer_nonnull: bool = True
    default_return_ownership: str = 'caller'
    default_layout_severity: Severity = Severity.ERROR
    default_nullability_severity: Severity = Severity.ERROR
    default_ownership_severity: Severity = Severity.WARNING
    enable_layout_generation: bool = True
    enable_nullability_generation: bool = True
    enable_ownership_generation: bool = True
    include_provenance: bool = True
    include_confidence: bool = True
    strict_mode: bool = True
```

- **Key Fields:**
    - `synthesis_version`: Pin the synthesis logic to a specific version for determinism.
    - `default_pointer_nonnull`: Assume pointers are non-null by default.
    - `strict_mode`: Enforce strict validation during synthesis.

---

### SynthesisResult

Container for the output of a `SynthesisEngine.synthesize()` call.

- **Attributes:**
    - `success`: Boolean indicating if synthesis completed without fatal errors.
    - `contract`: The generated `ContractDocument` (if successful).
    - `clauses_generated`: Total count of generated clauses.
    - `errors`: List of error messages.
    - `warnings`: List of warning messages.
    - `metadata`: Dictionary containing contextual analysis and timing info.

---

## Versioning & Determinism

### RuleRegistry

Authoritative source for synthesis rules associated with specific versions.

- **Static Methods:**
    - `get_rule(rule_id: str) -> Optional[SynthesisRule]`: Retrieve a specific rule definition.
    - `get_rules_for_synthesis_version(version: str) -> List[SynthesisRule]`: Get all rules active in a specific version.

---

### version_compare

```python
def version_compare(v1: str, op: str, v2: str) -> bool
```

Utility for comparing semantic versions (e.g., `'1.1.0' > '1.0.0'`).

---

## Bridge Layers

### IRBridge

Responsible for validating and preparing Module 05 IR for consumption by the synthesis engine.

- **Methods:**
    - `consume_ir(ir_unit: InterfaceUnit, strict: bool = True) -> InterfaceUnit`: Validates entity integrity and type completeness.

---

### ContractBridge

Responsible for final assembly and schema validation of synthesized clauses.

- **Methods:**
    - `produce_contract(clauses: List[ContractClause], target_interface_id: str, ...) -> ContractDocument`:
      Assembles clauses into a compliant document.

---

## CLI Reference

### `pfcv-synth synthesize`
Generate a contract for a single IR file.
- `ir_file`: Path to input IR.
- `-o, --output`: Output file path.
- `--format`: `json` or `yaml`.

### `pfcv-synth batch`
Process an entire directory of IR files.
- `pattern`: Glob pattern (e.g., `"ir/*.json"`).
- `--output-dir`: Where to save generated contracts.
- `--parallel`: Enable multi-core processing.

### `pfcv-synth verify-determinism`
Stress test the engine to ensure identical IR always yields identical contracts.
- `--iterations`: Number of times to repeat synthesis.

---

## Exceptions

- **`IRBridgeError`**: Raised during IR validation.
- **`SynthesisError`**: Base class for synthesis-specific failures.
- **`ContractBridgeError`**: Raised if the final contract violates the schema.

---

*Version: 1.0.0*
*Last Updated: 2026-02-16*
