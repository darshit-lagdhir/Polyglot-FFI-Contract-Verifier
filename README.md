# PFCV Module 05: IR Normalization

Transform raw interface artifacts into canonical intermediate representation (IR)
for verification and contract synthesis.

[![PyPI version](https://badge.fury.io/py/pfcv-module-05.svg)](https://badge.fury.io/py/pfcv-module-05)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pfcv/pfcv/workflows/Test/badge.svg)](https://github.com/pfcv/pfcv/actions)
[![codecov](https://codecov.io/gh/pfcv/pfcv/branch/main/graph/badge.svg)](https://codecov.io/gh/pfcv/pfcv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Complete Type System**: Scalars, pointers, arrays, structures, unions, enums, function pointers
- **Smart Normalization**: Typedef resolution, padding computation, calling convention detection
- **Comprehensive Validation**: 7-stage validation with actionable diagnostics
- **ABI Change Detection**: Semantic diffing with breaking change classification
- **Performance Optimized**: 6-8× faster with caching, vectorization
- **Production Ready**: CLI, Docker, CI/CD, comprehensive tests (1000+)

## Quick Start

### Install

```bash
pip install pfcv-module-05
```

### Basic Usage

```bash
# Normalize a raw interface artifact
pfcv-ir normalize raw_interface.json

# Compare two IR versions
pfcv-ir diff v1_ir.json v2_ir.json --recommend

# Inspect IR contents
pfcv-ir inspect ir_artifact.json --list-functions
```

### Python API

```python
from module_05_ir_normalization import IROrchestrator, IRNormalizationConfig
from pathlib import Path

config = IRNormalizationConfig(
    input_artifact_path=Path("raw_interface.json"),
    output_dir=Path("./output"),
    enable_validation=True
)

orchestrator = IROrchestrator(config)
report = orchestrator.execute()

print(f"Normalized {report.types_normalized} types")
print(f"Normalized {report.symbols_normalized} symbols")
```

## Documentation

- [Install Guide](docs/module_05/installation.md)
- [Quick Start](docs/module_05/quickstart.md)
- [CLI Reference](docs/module_05/cli-reference.md)
- [API Reference](docs/module_05/api-reference.md)
- [Diagnostics](docs/module_05/troubleshooting.md)

## Architecture

Module 04 (Raw Artifact) → **Module 05 (IR Normalization)** → Module 06 (Contract Synthesis)

Module 05 transforms compiler-extracted interface data into a canonical, validated intermediate representation suitable for verification.

## Project Status

- **Version**: 1.0.0 (Stable)
- **Development Status**: Production/Stable
- **Test Coverage**: >95%
- **Total Tests**: 1000+

## Contributing

Contributions welcome! See CONTRIBUTING.md.

## License

MIT License - see LICENSE file.

## Citation

If you use PFCV in academic work, please cite:

```bibtex
@software{pfcv_module05,
  title = {PFCV Module 05: IR Normalization},
  author = {PFCV Authors},
  year = {2025},
  url = {https://github.com/pfcv/pfcv}
}
```

## Support

- Documentation: https://docs.pfcv.dev/module-05
- Issues: https://github.com/pfcv/pfcv/issues
- Discussions: https://github.com/pfcv/pfcv/discussions

