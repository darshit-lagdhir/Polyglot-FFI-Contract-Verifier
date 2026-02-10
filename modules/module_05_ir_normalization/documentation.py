"""
Module 05: Documentation Generation

Automatic documentation generation for IR normalization.
"""

from pathlib import Path
from typing import Any, Dict, List

# ============================================================================
# ERROR CATALOG
# ============================================================================

ERROR_CATALOG = {
    'E1001': {
        'title': 'Type Conversion Error',
        'category': 'conversion',
        'severity': 'error',
        'description': 'Failed to convert Module 04 type to IR entity',
        'common_causes': [
            'Unsupported type construct in source code',
            'Incomplete type information from Module 04',
            'Corrupted artifact data'
        ],
        'solutions': [
            'Verify Module 04 artifact is valid',
            'Check artifact version compatibility',
            'Re-run Module 04 ingestion',
            'Report issue if type should be supported'
        ]
    },
    'E2101': {
        'title': 'Structure Size Mismatch',
        'category': 'validation',
        'severity': 'error',
        'description': 'Computed structure size does not match compiler-reported size',
        'common_causes': [
            'Missing padding in field layout',
            'Flexible array member not handled',
            'Packing attribute not captured',
            'Bitfield layout error'
        ],
        'solutions': [
            'Compare with: clang -cc1 -fdump-record-layouts',
            'Check for __attribute__((packed))',
            'Inspect structure: pfcv-ir inspect --show-type <name>',
            'Verify Module 04 captured all fields'
        ]
    },
    'E2102': {
        'title': 'Overlapping Structure Fields',
        'category': 'validation',
        'severity': 'error',
        'description': 'Structure fields overlap in memory',
        'common_causes': [
            'Incorrect field offsets from Module 04',
            'Bitfield layout error',
            'Union mistakenly represented as structure'
        ],
        'solutions': [
            'Verify source structure definition',
            'Check if should be union instead of struct',
            'Re-run Module 04 ingestion'
        ]
    },
    'W1001': {
        'title': 'Type Deduplication Warning',
        'category': 'normalization',
        'severity': 'warning',
        'description': 'Multiple structurally identical types found',
        'common_causes': [
            'Typedef chains to same type',
            'Forward declarations and definitions'
        ],
        'solutions': [
            'This is usually benign',
            'Review typedef usage if unexpected'
        ]
    }
}

# ============================================================================
# DOCUMENTATION GENERATOR
# ============================================================================

class DocumentationGenerator:
    """Generates documentation from code and metadata."""

    def __init__(self):
        self.error_catalog = ERROR_CATALOG

    def generate_troubleshooting_guide(self) -> str:
        """Generate troubleshooting guide from error catalog."""
        lines = [
            "# IR Normalization Diagnostics Guide",
            "",
            "This guide helps resolve common issues with IR normalization.",
            "",
            "## Table of Contents",
            ""
        ]

        # Generate TOC
        for code in sorted(self.error_catalog.keys()):
            info = self.error_catalog[code]
            slug = code.lower()
            lines.append(f"- [{code}: {info['title']}](#{slug})")

        lines.extend(["", "## Error Reference", ""])

                for code in sorted(self.error_catalog.keys()):
            info = self.error_catalog[code]
            lines.extend(self._generate_error_section(code, info))

        return "\n".join(lines)

    def _generate_error_section(self, code: str, info: Dict[str, Any]) -> List[str]:
        """Generate documentation section for one error."""
        lines = [
            f"### {code}: {info['title']}",
            "",
            f"**Category:** {info['category']}  ",
            f"**Severity:** {info['severity']}",
            "",
            f"{info['description']}",
            "",
            "**Common Causes:**",
            ""
        ]

        for cause in info['common_causes']:
            lines.append(f"- {cause}")

        lines.extend(["", "**Solutions:**", ""])

        for i, solution in enumerate(info['solutions'], 1):
            lines.append(f"{i}. {solution}")

        lines.extend(["", "---", ""])

        return lines

    def generate_cli_reference(self) -> str:
        """Generate CLI reference documentation."""
        return """
# CLI Reference

Complete reference for the `pfcv-ir` command-line tool.

## Global Options

### `--version`
Show version information and exit.
```bash
pfcv-ir --version
```

### `--verbose`
Enable verbose output showing detailed progress.
```bash
pfcv-ir --verbose normalize input.json
```

### `--quiet`
Suppress all output except errors.
```bash
pfcv-ir --quiet normalize input.json
```

### `--config FILE`
Load configuration from specified file.
```bash
pfcv-ir --config .pfcv-ir.yaml normalize
```

## Commands

### `normalize`
Normalize raw interface artifact from Module 04.

**Usage:**
```bash
pfcv-ir normalize [OPTIONS] <input-artifact>
```

**Options:**
- `-o, --output DIR`: Output directory (default: `.pfcv/ir_cache`)
- `--compress / --no-compress`: Enable/disable compression (default: enabled)
- `--validate / --no-validate`: Enable/disable validation (default: enabled)
- `--cache-dir DIR`: Cache directory location
- `--no-cache`: Disable caching entirely
- `--diff-baseline FILE`: Compare with baseline artifact
- `--report FILE`: Output report to file
- `--profile`: Enable performance profiling

**Examples:**
```bash
pfcv-ir normalize raw_interface.json
pfcv-ir normalize raw_interface.json -o ./ir_output
pfcv-ir normalize new.json --diff-baseline old_ir.json
```

### `validate`
Validate existing IR artifact.

**Usage:**
```bash
pfcv-ir validate [OPTIONS] <ir-artifact>
```

**Options:**
- `--report FILE`: Output validation report

**Examples:**
```bash
pfcv-ir validate ir_artifact.json
```

### `diff`
Compare two IR artifacts.

**Usage:**
```bash
pfcv-ir diff [OPTIONS] <old-artifact> <new-artifact>
```

**Options:**
- `--format FORMAT`: Output format: text, json, markdown (default: text)
- `--output FILE`: Write diff to file
- `--filter TYPE`: Show only: breaking, compatible, all (default: all)
- `--recommend`: Show version bump recommendation

**Examples:**
```bash
pfcv-ir diff v1_ir.json v2_ir.json --recommend
```

### `inspect`
Inspect and query IR artifact contents.

**Usage:**
```bash
pfcv-ir inspect [OPTIONS] <ir-artifact>
```

**Options:**
- `--list-types`: List all types
- `--list-functions`: List all functions
- `--show-type NAME`: Show detailed type information

### `cache`
Manage artifact cache.

**Usage:**
```bash
pfcv-ir cache <subcommand>
```

**Subcommands:**
- `stats`: Show cache statistics
- `clear`: Clear entire cache

## Exit Codes
- 0: Success
- 1: Validation failed
- 2: Normalization error
- 3: Config error
- 4: File not found

## Environment Variables
- `PFCV_CACHE_DIR`: Override default cache directory
- `PFCV_CONFIG`: Default configuration file location

## Config Files
Config can be provided via YAML or JSON files.
"""

    def generate_api_reference(self) -> str:
        """Generate Python API reference."""
        return """
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
"""

    def save_all_documentation(self, output_dir: Path):
        """Generate and save all documentation."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Diagnostics guide
        troubleshooting = self.generate_troubleshooting_guide()
        (output_dir / "troubleshooting.md").write_text(troubleshooting)

        # CLI reference
        cli_ref = self.generate_cli_reference()
        (output_dir / "cli-reference.md").write_text(cli_ref)

        # API reference
        api_ref = self.generate_api_reference()
        (output_dir / "api-reference.md").write_text(api_ref)

        print(f"Documentation generated in {output_dir}/")

__all__ = [
    'DocumentationGenerator',
    'ERROR_CATALOG'
]
