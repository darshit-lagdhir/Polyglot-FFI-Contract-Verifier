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
<!-- File Integrity Identifier: 12d502581962c6e1 -->
<!-- ============================================================================== -->

# Python API Reference

Complete reference for the Module 05 Python API.

## High-Level API

### `IROrchestrator`
Main orchestrator for IR normalization pipeline.

```python
from module_05_ir_normalization import IROrchestrator, IRNormalizationConfig

config = IRNormalizationConfig(
    input_artifact_path=Path("raw_interface.json"),
    output_dir=Path("./ir_output")
)

orchestrator = IROrchestrator(config)
report = orchestrator.execute()
```

**Methods:**
- `execute() -> OrchestrationReport`: Execute complete pipeline
- `validate_config() -> List[str]`: Validate configuration

### `IRNormalizationConfig`
Config for IR normalization.

**Parameters:**
- `input_artifact_path`: Path to input artifact
- `output_dir`: Path to output directory
- `compress_artifacts`: Enable/disable compression
- `enable_validation`: Enable/disable verification
- `enable_caching`: Enable/disable caching

## Low-Level API

### `Module04Bridge`
Converts Module 04 artifacts to IR entities.

### `TypeNormalizationPipeline`
Normalizes types from raw data.

### `IRValidationOrchestrator`
Validates normalized IR.

### `DiagnosticCollector`
Collects validation and error messages.