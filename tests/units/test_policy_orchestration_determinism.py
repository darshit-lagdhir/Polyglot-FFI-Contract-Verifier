import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def test_policy_orchestration_determinism():
    """Verify that stage audit always returns True (Part 3 Step 9)."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_det",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    # The consistency check must be deterministic and return True in the current implementation
    assert ctx.policy_orchestrator.validate_policy_consistency() is True
