# Module 06: Examples

This directory contains working examples demonstrating the capabilities of the PFCV Contract Schema module.

## Examples Overview

### 01. Basic Generation
Generate a contract from an IR artifact.

**What you'll learn**:
- Configuring contract generation.
- Generating contracts from IR metadata.
- Saving contracts to persistent storage.

**Complexity**: ⭐ Beginner
**Directory**: `01_basic_generation/`

---

### 02. Validation
Validate a contract through multiple validation layers.

**What you'll learn**:
- Loading contracts from files.
- Configuring validation contexts.
- Interpreting multi-layer validation results.

**Complexity**: ⭐ Beginner
**Directory**: `02_validation/`

---

### 03. Diffing (Coming Soon)
Compare two contract versions and detect semantic changes.

---

### 04. Enforcement (Coming Soon)
Set up runtime constraint enforcement for FFI call boundaries.

---

## Running Examples

Each example is designed to be self-contained. Navigate to the example directory and run the main Python script:

```bash
cd 01_basic_generation
python generate.py
```

## Prerequisites

- **Python 3.9+**
- **Module 06** must be in your Python path.

## Troubleshooting

If examples fail to import `module_06_contract_schema`, ensure your `PYTHONPATH` includes the `modules` directory of the project:

```bash
# From the project root
$env:PYTHONPATH="modules"
python examples/module_06/01_basic_generation/generate.py
```
