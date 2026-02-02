# VERIFICATION PIPELINE - MODULE 02

**Version:** 1.0.0  
**Module:** 02 of 28  
**Status:** In Progress ( Complete)  
**Author:** Darshit Lagdhir  
**Date:** 2026-02-02  

---

## Document Overview

This document provides the complete technical specification for the Verification Pipeline module of the Polyglot FFI Contract Verifier.

**Progress:**
- ✅ : Pipeline Philosophy & Formal Model (COMPLETE)
- ✅ : Stage State Machines & Artifact Validation (COMPLETE)
- ✅ : Artifact Schemas & Incremental Verification (COMPLETE)
- ✅ : Native Interface Ingestion Stage (COMPLETE)
- ✅ : IR Normalization Stage (COMPLETE)
- ✅ : Contract Synthesis Stage (COMPLETE)
- ✅ : Adapter Generation Stage (COMPLETE)
- ⏳ Prompts 8-20: Additional pipeline components (PENDING)

---

## Table of Contents

1. [Pipeline Philosophy & Formal Model](#1-pipeline-philosophy--formal-model)
2. [Stage State Machines & Artifact Validation](#2-stage-state-machines--artifact-validation)
3. [Artifact Schemas & Incremental Verification](#3-artifact-schemas--incremental-verification)
4. [Native Interface Ingestion Stage](#4-native-interface-ingestion-stage)
5. [IR Normalization Stage](#5-ir-normalization-stage)
6. [Contract Synthesis Stage](#6-contract-synthesis-stage)
7. [Adapter Generation Stage](#7-adapter-generation-stage)
8. [Implementation Architecture](#8-implementation-architecture)
9. [Usage Examples](#9-usage-examples)
10. [Next Steps](#10-next-steps)

---

## 1-6. Previous Sections

*(See previous versions for full text - preserved)*

---

## 7. Adapter Generation Stage

### 7.1 Overview - Enforcing Contracts at Runtime

The Adapter Generation stage mechanically translates abstract logic constraints into concrete Python `ctypes` wrappers. These adapters serve as the protection layer between safe managed code and unsafe native code.

### 7.2 Safety Mechanisms

1.  **Pre-Call Checks**: Verify constraints (e.g., non-null, buffer size) *before* the native call is attempted.
2.  **Structured Exceptions**: Raise `ContractViolation` with detailed metadata instead of crashing.
3.  **Ownership Tracking**: Track allocations and deallocations to prevent memory leaks and double-frees.
4.  **Type Safety**: Map IR types to precise `ctypes` equivalents to prevent ABI mismatches.

### 7.3 Generated Artifacts

- **`library_adapter.py`**: Contains python wrapper functions with injected checks.
- **`adapter_metadata.json`**: Describes which constraints were enforced and mapping details.

### 7.4 Example Generated Code

```python
def process_data(data, length):
    """
    Wrapper for: int process_data(char* data, size_t length)
    Constraints:
      - process_NON_NULL_data_1
      - process_BUFFER_SIZE_data_2
    """
    # Pre-call checks
    _check_NON_NULL_data(data)
    _check_BUFFER_SIZE_data(data, length)
    
    # Native call
    result = _lib.process_data(data, length)
    return result
```

---

## 8. Implementation Architecture

### 8.1 Class Hierarchy

```
PipelineStage (ABC)
├── NativeInterfaceIngestionStage
├── IRNormalizationStage
├── ContractSynthesisStage
└── AdapterGenerationStage (NEW)
    ├── Uses: CodeGenerator
    ├── Uses: TypeMapper
    ├── Uses: CheckGenerator
    └── Uses: AdapterGenerator
```

---

## 9. Usage Examples

### 9.1 Running Adapter Generation

```bash
python modules/module_02_verification_pipeline/verification_pipeline.py run-incremental \
    --context artifacts/execution_context.json \
    --target adapter_metadata
```

---

## 10. Next Steps

**** will implement:
- **Test Plan Generation Stage**: Systematically deriving test cases to verify the generated adapters and detecting edge cases.
