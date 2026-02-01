# Operational Best Practices

## Overview
This guide provides practical recommendations for users and maintainers to get the most out of the Polyglot FFI Contract Verifier. Following these practices ensures reliable, efficient, and maintainable verification pipelines.

## For Users

### 1. Workflow Integration
- **Run Locally First**: Always run verification locally (`polyglot_ffi_verifier.py verify`) before pushing to CI.
- **Fail Fast**: Configure your CI to run FFI verification early in the pipeline, as native crashes can destabilize later steps.
- **Use Badges**: Add the status badge to your README to keep FFI safety visible to the team.

### 2. Header Management
- **Self-Contained Headers**: Ensure your interface header includes all necessary types. The ingestor is not a full compiler preprocessor.
- **Stable Interfaces**: Avoid changing function signatures frequently. If you do, regenerate the contract and adapters.
- **Documentation Comments**: Use Doxygen-style comments in your C header. While currently ignored, future versions may use them for constraint inference.

### 3. Contract Management
- **Version Control Contracts**: Check `contract.json` into git. It is the source of truth for your interface safety.
- **Review Changes**: When `contract.json` changes, review the diff manually to ensure valid constraints weren't lost.
- **Baseline Comparison**: Use `compare-contracts` command to detect accidental breaking changes.

### 4. Test Data Management
- **Deterministic Tests**: Ensure your native library behavior is deterministic for the same inputs.
- **Mock External Dependencies**: If your native library calls network/DB, mock these out for FFI verification. The verifier checks the *boundary*, not the backend.

### 5. Diagnostics
- **Enable Debugging**: Use `--debug` flag if ingestion is failing. It prints libclang details.
- **Isolate Crashes**: If verification hangs, check the `execution_log.json` to see which test ran last. The crash is likely in that function.

## For Maintainers

### 1. Extending the System
- **Follow Phase Isolation**: If adding a feature, place it in the appropriate phase. Do not mix ingestion logic with verification logic.
- **Update Artifacts**: If you change an artifact schema, update the version number in `ProvenanceMetadata`.
- **Add Validation**: Every new phase must have a corresponding `validate_*.py` script.

### 2. Code Style
- **Type Hints**: Use Python type hints everywhere.
- **Docstrings**: Document every class and public method.
- **No Global State**: Pass `ExecutionContext` explicitly. Do not rely on module-level variables.

### 3. Release Process
- **Run Full Validation**: Execute all `validate_*.py` scripts before tagging a release.
- **Update Documentation**: Ensure all `docs/*.md` files are current with code changes.
- **Semantic Versioning**: Bump major version if `contract.json` schema changes incompatibly.

### 4. Dependencies
- **Pin Versions**: Pin `libclang` and `PyYAML` versions in `requirements.txt` to avoid upstream breakage.
- **Vendor Critical Libs**: If a library is small and critical, consider vendoring it to reduce install friction.
