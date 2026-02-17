# PFCV Troubleshooting Guide

This guide helps you resolve common issues encountered while using the **Polyglot FFI Contract Verifier (PFCV)** pipeline.

## Pipeline-Wide Issues

### 1. IR Extraction Failures (Module 04/05)
**Error**: `Clang error: cannot find header`
**Solution**: Ensure your include paths are correctly passed to the IR extractor. Check your `CPATH` environment variable or use the `-I` flag.

### 2. Contract Schema Mismatches (Module 06)
**Error**: `ContractBridgeError: Schema validation failed`
**Solution**: This usually occurs if an older contract is being used with a newer version of the pipeline. Regenerate the contract using Module 07.

## Synthesis-Specific Issues (Module 07)

### 3. IR Validation Failures
**Error**: `IRBridgeError: IR validation failed: Type completeness violation`
**Cause**: The input IR references a type ID that is not defined in the `types` list.
**Solution**: Use `pfcv-ir validate` to check the integrity of your IR artifact before synthesis.

### 4. Determinism Violations
**Symptoms**: Identical IR produces slightly different contract JSON.
**Solution**: Ensure you are using a pinned `synthesis_version` in your configuration. Use `pfcv-synth verify-determinism` to debug.

### 5. Performance Bottlenecks
**Symptoms**: Synthesis taking more than a few seconds for large interfaces.
**Solution**:
- **Enable Caching**: Ensure `SynthesisCache` is properly configured.
- **Parallel Synthesis**: Use the `batch --parallel` CLI command.

## Infrastructure Issues

### 6. Memory Limits
**Symptoms**: `Process finished with exit code 137` (OOM Killer).
**Solution**: Processing extremely large headers (>5,000 functions) may require up to 4GB of RAM. Increase container memory limits.

## Debugging Tips

1. **Enable Verbose Logging**: Use the `--verbose` flag on CLI commands or set `logging.basicConfig(level=logging.DEBUG)`.
2. **Inspect Provenance**: Every generated clause includes a `provenance` field. Inspect this to see *why* a specific constraint was generated.
3. **Verify Installation**: Run `pfcv --version` to ensure all modules are correctly installed and visible.

---
© 2026 PFCV Team.
