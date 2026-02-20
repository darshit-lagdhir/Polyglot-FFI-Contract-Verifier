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
<!-- File Integrity Identifier: 5df8326ee842f1c9 -->
<!-- ============================================================================== -->

# Module 06: Contract Schema & Synthesis

Transform implicit FFI assumptions into explicit, machine-verifiable contracts.

[![Tests](https://img.shields.io/badge/tests-401%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🎯 Overview

Module 06 provides a complete contract system for FFI (Foreign Function Interface) 
verification. It transforms implicit assumptions about FFI boundaries into 
explicit, validated, and enforceable contracts.

**Key Capabilities**:
- 🤖 **Automated Generation**: Create contracts from IR artifacts
- ✅ **Multi-Layer Validation**: Schema, referential, and constraint validation
- 📊 **Semantic Versioning**: Track contract evolution with compatibility analysis
- 🔍 **Advanced Diffing**: Detect breaking changes with migration guidance
- 🛡️ **Runtime Enforcement**: Check constraints at FFI call boundaries
- 🖥️ **CLI & API**: Both command-line and Python API interfaces

## 🚀 Quick Start

### Installation

```bash
pip install pfcv-module-06
```

### Generate a Contract

```python
from module_06_contract_schema import ContractGenerator

# Create generator
generator = ContractGenerator()

# Generate from IR artifact (mock IR used for demonstration)
contract = generator.generate(ir_artifact=None, target_interface_id="my_interface")

print(f"Generated {len(contract.clauses)} clauses")
```

### Validate a Contract

```python
from module_06_contract_schema import ContractValidator

validator = ContractValidator()
result = validator.validate(contract, skip_referential=True)

if result.passed:
    print("✓ Contract is valid")
else:
    print(f"✗ Validation failed: {len(result.get_all_errors())} errors")
```

### Compare Contract Versions

```python
from module_06_contract_schema import AdvancedContractDiffer

differ = AdvancedContractDiffer()
diff = differ.compute_diff(old_contract, new_contract)

if diff.overall_impact.value == "breaking":
    print("⚠️ Breaking changes detected")
    if diff.migration_guide:
        print(diff.migration_guide.format())
```

### CLI Usage

```bash
# Generate contract
pfcv-contract generate ir_artifact.json -o contract.json

# Validate contract
pfcv-contract validate contract.json

# Compare versions
pfcv-contract diff v1.json v2.json --migration

# Inspect contract
pfcv-contract inspect contract.json --stats
```

## 📚 Documentation

- **User Guide**: Comprehensive usage guide for developers.
- **API Reference**: Detailed documentation of all public classes and functions.
- **Examples**: Working code samples for common use cases.
- **Architecture**: System design and component interaction documentation.
- **Troubleshooting**: Solutions for common issues and performance tips.

## 🎓 Examples

### Basic Contract Generation

```python
from module_06_contract_schema import ContractGenerator, save_contract
from pathlib import Path

# Generate contract
generator = ContractGenerator()
contract = generator.generate(ir_artifact=None, target_interface_id="my_library")

# Save to file
save_contract(contract, Path("my_library.contract.json"))
```

### Contract Enforcement

```python
from module_06_contract_schema import (
    EnforcementEngine, PythonAdapter, EnforcementMode
)

# Create enforcement engine
adapter = PythonAdapter(mode=EnforcementMode.STRICT)
engine = EnforcementEngine(contract, adapter)

# Enforce constraints before FFI call
violations = engine.enforce_pre_call(
    "process_data",
    {"buffer": my_buffer, "length": len(my_buffer)}
)

if violations:
    for v in violations:
        print(f"Violation: {v.format_error_message()}")
```

## 🏗️ Architecture

Module 06 consists of 9 major components:

1.  **Entity Model**: Core contract representation (Document, Header, Clause).
2.  **Typed Clauses**: Strongly-typed constraint clauses (Size, Alignment, Nullability, etc.).
3.  **Validation**: Three-layer validation framework (Schema, Referential, Constraint).
4.  **Versioning**: Semantic versioning system for contracts.
5.  **Serialization**: JSON persistence with integrity verification (SHA-256).
6.  **Generation**: Automated contract creation from IR artifacts.
7.  **Diffing**: Advanced contract comparison with impact analysis.
8.  **CLI**: Command-line interface for all primary operations.
9.  **Enforcement**: Runtime constraint checking via language adapters.

## 🧪 Testing

Module 06 has comprehensive test coverage:

- **Unit Tests**: 860+ tests across all components.
- **Integration Tests**: 13 end-to-end workflow tests.
- **Package Tests**: 50 initialization and import tests.
- **Total**: Over 950 tests, all passing.

Run tests:

```bash
pytest tests/unit/test_contract_*.py -v
pytest tests/integration/test_module_06_integration.py -v
```

## 📊 Performance

Benchmarked on typical workloads:

- **Contract Generation**: <1s for 500-clause contracts.
- **Validation**: <1s for typical contracts.
- **Serialization**: <500ms for 500-clause contracts.
- **Enforcement Overhead**: <10000ns per call (Python Adapter).

## 🤝 Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

1.  Fork the repository.
2.  Create a feature branch.
3.  Add tests for new features.
4.  Ensure all tests pass.
5.  Submit a pull request.

## 📄 License

MIT License - see `LICENSE` for details.

---
**PFCV Team** | [GitHub](https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier) | [Email](mailto:team@pfcv.dev)