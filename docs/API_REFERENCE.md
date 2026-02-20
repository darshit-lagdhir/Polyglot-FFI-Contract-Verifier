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
<!-- File Integrity Identifier: 1e8de934a30a83fc -->
<!-- ============================================================================== -->

# PFCV API Reference Index

This document provides a centralized index for all public APIs in the **Polyglot FFI Contract Verifier** suite.

## 📋 Module APIs

| Module | Purpose | API Entry Point | Reference |
| :--- | :--- | :--- | :--- |
| **Module 01** | Architecture | `ArchitectureValidator` | [Details](../modules/module_01_ffi_verifier/SYSTEM_ARCHITECTURE.md) |
| **Module 02** | Pipeline | `run_verification_pipeline()` | [Details](../modules/module_02_verification_pipeline/VERIFICATION_PIPELINE.md) |
| **Module 03** | Build | `BuildManager` | [Details](../modules/module_03_build_process/BUILD_PROCESS.md) |
| **Module 04** | Ingestion | `IngestionEngine` | [Details](../modules/module_04_native_interface_ingestion/NATIVE_INTERFACE_INGESTION.md) |
| **Module 05** | IR | `IRInterfaceUnit` | [Details](module_05/api-reference.md) |
| **Module 06** | Schema | `ContractDocument` | [Details](API_REFERENCE.md#module-06) |
| **Module 07** | Synthesis | `SynthesisEngine` | [Details](#module-07-synthesis-engine) |

---

## 🏗️ Global Verification Utilities

### `pfcv.verify()`
The primary high-level entry point for end-to-end verification.

```python
from pfcv import verify

result = verify(
    source="include/lib.h",
    library="lib/lib.so",
    config="configs/default.yaml"
)
```

---

## 🛠️ Module 07: Synthesis Engine (Detailed)

### `synthesize_from_ir`
```python
def synthesize_from_ir(
    ir_path: Union[str, Path],
    config: Optional[SynthesisConfig] = None,
    strict: bool = True
) -> ContractDocument
```
Synthesize a contract from an Intermediate Representation (IR) file.

### `SynthesisEngine`
The main orchestrator responsible for the multi-phase synthesis process.
- **`synthesize(ir_unit, target_id)`**: Performs in-memory synthesis.

---

## 🚔 Module 06: Contract Schema & Enforcement

### `validate_contract`
```python
def validate_contract(contract_path: Union[str, Path]) -> bool
```
Verify a contract matches the formal PFCV schema.

### `EnforcementAdapter`
Runtime wrapper for native functions using synthesized contracts.

---

## ⚠️ Internal Bridges

- **`IRBridge`**: Module 05 -> Module 07 validation layer.
- **`ContractBridge`**: Module 07 -> Module 06 assembly layer.

---
*Version: 1.0.0*  
*Last Updated: 2026-02-17*