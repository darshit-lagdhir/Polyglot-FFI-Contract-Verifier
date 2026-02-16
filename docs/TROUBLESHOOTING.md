# Troubleshooting Guide: Module 07 Contract Synthesis

This guide helps you resolve common issues encountered while using the Contract Synthesis Engine.

## Common Issues and Solutions

### 1. IR Validation Failures

**Error**: `IRBridgeError: IR validation failed: Type completeness violation`

**Cause**: The input IR references a type ID that is not defined in the `types` list.
**Solution**:
- Check the `type_reference` fields in your IR parameters or fields.
- Ensure every referenced type exists in the `InterfaceUnit.types` collection.
- Use `IRValidator.validate(ir_unit)` manually to get a detailed list of missing types.

### 2. Unexpected Synthesis Errors

**Error**: `Contract assembly failed`

**Cause**: The synthesized clauses violate the Module 06 Contract Schema (e.g., missing ID, invalid parameters).
**Solution**:
- If you are using custom rule logic, ensure it complies with the schema.
- Run synthesis in `strict_mode=False` within `SynthesisConfig` to see if it bypasses the error (not recommended for production).
- Check the log output for specific schema validation errors.

### 3. Performance is Slow

**Symptoms**: Synthesis taking $> 1s$ for large interfaces.

**Solutions**:
- **Enable Caching**: Use the `SynthesisCache` to store and retrieve results for unchanged interfaces.
- **Profiling**: Use `PhaseProfiler` to identify which synthesis phase (e.g., Relational, Layout) is taking the most time.
- **Batch Processing**: If processing many small files, reuse the same `SynthesisEngine` instance to avoid initialization overhead.

### 4. Determinism Issues

**Symptoms**: Identical IR produces slightly different contract JSON (e.g., clause ordering).

**Solution**:
- Ensure you are using the same `synthesis_version` in your `SynthesisConfig`.
- Use the `pfcv-synth verify-determinism` CLI tool to isolate the issue.
- Verify that your IR generation process (Module 05) is deterministic.

### 5. Infinite Loops or Stack Overflows

**Symptoms**: Python hangs during "Relational Clause Generation".

**Possible Cause**: Cyclic dependencies or flawed logic in relational clause derivation (fixed in recent versions, but check your implementation).
**Solution**:
- Update to the latest version of Module 07.
- Check for extremely large recursive structures in the IR.

## Debugging Tips

1. **Enable Debug Logs**:
   Add `logging.basicConfig(level=logging.DEBUG)` to see detailed trace of synthesis phases.

2. **Inspect Provenance**:
   Every clause has a `metadata['provenance']` field. Inspecting this tells you exactly which IR entity and which synthesis rule caused the clause to appear.

3. **Use the Completeness Validator**:
   Run `python -m module_07_contract_synthesis.completion_check` to ensure your environment is set up correctly.

## Getting Help

If you still encounter issues:
- Review the `examples/module_07` scripts for reference implementations.
- Consult the `SYNTHESIS_ENGINE.md` for API details.
- Check the unit tests in `tests/` to see how specific edge cases are handled.
