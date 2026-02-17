# Production Deployment Guide: PFCV Pipeline

This guide provides authoritative patterns for deploying, monitoring, and scaling the **Polyglot FFI Contract Verifier (PFCV)** pipeline in enterprise environments.

## Deployment Architecture Patterns

### 1. Integrated CI/CD Pipeline (Recommended)
The most common pattern is to integrate the full 7-module verification pipeline directly into your CI/CD system. This ensures that any change to native headers or implementation triggers an immediate verification cycle.

**GitHub Actions Example:**
```yaml
name: PFCV Verification

on:
  push:
    paths: ['include/**/*.h', 'src/**/*.rs', 'src/**/*.c']

jobs:
  verify-ffi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      
      - name: Install PFCV
        run: pip install polyglot-ffi-contract-verifier
        
      - name: Step 1: Extract IR (Module 04/05)
        run: pfcv-ir extract include/ --output build/ir/
        
      - name: Step 2: Synthesize Contracts (Module 07)
        run: pfcv-synth batch "build/ir/*.json" --output-dir contracts/ --strict
        
      - name: Step 3: Run Verification (Module 02)
        run: pfcv-verify --contract contracts/main.json --lib build/lib/libtarget.so
```

### 2. Standalone Synthesis & Registry service
For large organizations, we recommend a centralized "Contract Registry" service where synthesized contracts are stored and versioned.

---

## Migration Guide

### Migrating from Manual Contract Writing
If you are currently maintaining YAML/JSON contracts by hand:
1. **Pilot Phase**: Run the synthesis engine on a small subset of headers.
2. **Comparison**: Use `pfcv-synth diff manual.json auto.json` to identify where automated heuristics differ from your manual assumptions.
3. **Refinement**: Adjust `SynthesisConfig` (e.g., `default_pointer_nonnull`) until the automated output covers 90% of your needs.

### Transitioning from SWIG/Bindgen
PFCV acts as a safety companion to binding generators. While SWIG generates the bridge code, PFCV validates the *assumptions* made by that bridge code.

---

## Monitoring & Observability

### Performance Metrics
Track the health of your verification tasks:
- **Synthesis Latency**: Time to generate contracts from IR.
- **Verification Pass Rate**: Percentage of FFI boundaries meeting safety constraints.
- **Cache Hit Rate**: Efficiency of Module 07 LRU caching.

---

## Security Guidelines

1. **IR Sanitization**: Never synthesize from untrusted IR without `strict_mode=True`.
2. **Contract Integrity**: Digitally sign your synthesized contracts in production.
3. **Least Privilege**: Run the verification pipeline in a container with no network access once dependencies are installed.

---

## Scaling Strategy

1. **Horizontal Scaling**: Distribution of verification tasks across a build farm.
2. **Incremental Verification**: Use Module 02's incremental mode to only re-verify affected functions.
3. **Cold/Warm Caching**: Persistent L2 caching for massive monorepos.

---
© 2026 PFCV Team.
