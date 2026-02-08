
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
