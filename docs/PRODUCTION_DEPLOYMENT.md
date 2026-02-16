# Production Deployment Guide: Module 07 Contract Synthesis

This guide provides authoritative patterns for deploying, monitoring, and scaling the Contract Synthesis Engine in enterprise environments.

## Deployment Architecture Patterns

### 1. Integrated CI/CD Pipeline (Recommended)
The most common pattern is to integrate synthesis directly into the native build pipeline. Contracts are generated whenever the native interface (C/C++, Rust headers) changes.

**GitHub Actions Example:**
```yaml
name: FFI Contract Synthesis

on:
  push:
    paths: ['include/**/*.h', 'src/**/*.rs']

jobs:
  synthesize-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      
      - name: Install Tools
        run: pip install pfcv-ir-extractor pfcv-contract-synthesis
        
      - name: Extract IR (Module 05)
        run: pfcv-ir include/ --output build/ir/
        
      - name: Synthesize (Module 07)
        run: pfcv-synth batch "build/ir/*.json" --output-dir contracts/ --strict
        
      - name: Verify Determinism
        run: pfcv-synth verify-determinism build/ir/main.json
        
      - name: Commit Updated Contracts
        run: |
          git config user.name "Synthesis Bot"
          git add contracts/
          git commit -m "chore: auto-update FFI contracts [skip ci]"
          git push
```

### 2. Standalone Synthesis Microservice
For organizations with many polyglot projects, a centralized synthesis service provides "Synthesis as a Service."

**FastAPI Implementation:**
```python
from fastapi import FastAPI, UploadFile, HTTPException
from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
from module_05_ir_normalization.ir_serialization import IRSerializer

app = FastAPI(title="PFCV Synthesis Service")
engine = SynthesisEngine(SynthesisConfig(strict_mode=True))

@app.post("/v1/synthesize")
async def handle_synthesis(file: UploadFile):
    content = await file.read()
    ir_unit = IRSerializer().deserialize(content.decode())
    
    result = engine.synthesize(ir_unit, file.filename)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.errors)
        
    return {"contract": result.contract.to_dict()}
```

---

## Migration Guide

### Migrating from Manual Contract Writing
If you are currently maintaining YAML/JSON contracts by hand:
1. **Pilot Phase**: Run the synthesis engine on a small subset of headers.
2. **Comparison**: Use `pfcv-synth diff manual.json auto.json` to identify where automated heuristics differ from your manual assumptions.
3. **Refinement**: Adjust `SynthesisConfig` (e.g., `default_pointer_nonnull`) until the automated output covers 90% of your needs.
4. **Customization**: For the remaining 10%, use the [Advanced Customization](#advanced-customization) features below.

### Migrating from C2Rust or SWIG
1. **Extract**: Use Module 05 to extract IR from the original C/C++ headers.
2. **Synthesize**: Generate PFCV contracts using Module 07.
3. **Enforce**: Use Module 06 `ContractEnforcer` to wrap your generated bindings with the synthesized safety checks.

---

## Monitoring & Observability

### Prometheus Metrics
Track the health of your synthesis pipeline:

```python
from prometheus_client import Counter, Histogram

SYNTH_TOTAL = Counter('pfcv_synthesis_total', 'Total operations', ['status'])
SYNTH_LATENCY = Histogram('pfcv_synthesis_seconds', 'Time spent synthesizing')

def monitored_synth(ir_unit, name):
    with SYNTH_LATENCY.time():
        result = engine.synthesize(ir_unit, name)
        status = "success" if result.success else "failure"
        SYNTH_TOTAL.labels(status=status).inc()
    return result
```

### Structured Logging (JSON)
Logs should include `interface_id` and `clauses_generated` for auditability.
```json
{
  "timestamp": "2026-02-16T20:30:00Z",
  "level": "INFO",
  "event": "synthesis_complete",
  "interface_id": "libcrypto_v2",
  "clauses_generated": 142,
  "duration_ms": 12.4
}
```

---

## Security Guidelines

1. **IR Sanitization**: Synthesis should never be performed on untrusted IR artifacts without strict validation. Always keep `strict_mode=True` in production.
2. **Contract Signing**: After synthesis, sign the contract JSON to prevent tampering:
   ```python
   import hashlib
   sig = hashlib.sha256(contract_json.encode()).hexdigest()
   contract.metadata['signature'] = sig
   ```
3. **Resource Isolation**: Large IR files can cause high memory usage. Set container memory limits (e.g., 2GB) when running as a service.

---

## Advanced Customization

### Developing Custom Clause Generators
You can extend the synthesis engine by injecting custom generators.

```python
from module_07_contract_synthesis.synthesis_engine import ClauseGenerator

class SecurityHardeningGenerator(ClauseGenerator):
    """Adds mandatory salt-length checks for crypto functions."""
    def generate(self, ir_unit, all_clauses):
        for fn in ir_unit.symbols:
            if "hash" in fn.source_name:
                # Add custom security clause...
                pass
```

### Plugin System
Register plugins to the `SynthesisEngine` to participate in the lifecycle:
1. `pre_synthesis(ir_unit)`
2. `post_synthesis(contract)`

---

## Performance Tuning

1. **Enable Multi-level Caching**: Re-using `SynthesisCache` can reduce latency by 95% for unchanged interfaces.
2. **Batch Parallelism**: Use the `--parallel` flag on the CLI to distribute synthesis across all available CPU cores.
3. **Avoid Re-initialization**: Reuse a single `SynthesisEngine` instance for multiple synthesis calls to benefit from warmed internal registries.
