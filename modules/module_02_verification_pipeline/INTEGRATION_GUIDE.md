# Integration Guide - Module 02 → Module 03

This guide explains how Module 03 (Formal Verification) will integrate with Module 02 (Testing Pipeline).

## Architecture

```
   Module 02 (Testing)         Module 03 (Formal Verification)
┌─────────────────┐           ┌──────────────────────┐
│   Stages 1-7    │           │     Stages 8-12      │
│                 │           │                      │
│  contract.json  ──┼─────────→│  Symbolic Execution  │
│      ir.json    ──┼─────────→│     SMT Solving      │
│  test_plan.json ──┼─────────→│   Proof Generation   │
│                 │           │                      │
│                 │←─────────┼──    proof.json       │
│                 │←─────────┼── counterexample.json │
└─────────────────┘           └──────────────────────┘
```

## Integration Points

### 1. Artifact Consumption

Module 03 consumes Module 02 artifacts:

```json
// contract.json - Safety contracts to prove
{
  "functions": [
    {
      "name": "process",
      "constraints": [
        {"type": "NON_NULL", "target": "param_data"},
        {"type": "BUFFER_SIZE", "target": "param_data", "related_target": "param_length"}
      ]
    }
  ]
}
```

### 2. Plugin Registration

Module 03 registers as a plugin:

```python
from modules.module_02_verification_pipeline.verification_pipeline import verify_extensible
from modules.module_03_formal_verification import FormalVerificationPlugin

result = verify_extensible(
    "interface.h", "library.dll",
    plugins=[FormalVerificationPlugin()]
)
```

### 3. Hook Integration

Module 03 uses hooks for tight integration:

```python
class FormalVerificationPlugin(PipelinePlugin):
    def get_hooks(self):
        return {
            "post_contract_synthesis": self.enrich_contracts,
            "post_test_plan_generation": self.add_symbolic_tests
        }
```

## Contract Schema

Module 03 must consume `contract.json` schema v1.0.0:

```json
{
  "schema_version": "1.0.0",
  "functions": [
    {
      "name": "string",
      "constraints": [
        {
          "constraint_id": "string",
          "type": "string",
          "target": "string",
          "confidence": "float",
          "rationale": "string"
        }
      ]
    }
  ]
}
```

## Testing Strategy

Module 03 tests should:
1. Unit test symbolic execution engine
2. Integration test with Module 02 artifacts
3. E2E test full pipeline (testing + proving)

## Performance Considerations
- Cache proofs (they're expensive)
- Run symbolic execution in parallel
- Timeout long-running proofs

## Example Integration

```python
# Combined testing + formal verification
from modules.module_02_verification_pipeline.verification_pipeline import verify_extensible
from modules.module_03_formal_verification import FormalVerificationPlugin

result = verify_extensible(
    "interface.h", "library.dll",
    plugins=[FormalVerificationPlugin()],
    enable_formal_verification=True,
    proof_timeout_seconds=300
)

print(f"Tests: {result.pass_rate}% passed")
print(f"Proofs: {result.proofs_generated} contracts proven")
print(f"Counterexamples: {result.counterexamples_found} contracts disproven")
```

**Status:** Ready for Module 03 development
