import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def test_policy_stage_order_immutable():
    """Verify that enforcement stages are defined in immutable sequence."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_order",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    orch = ctx.policy_orchestrator
    
    expected = [
        "CONFIG_VAL", "ABI_NEG", "IVAR_PRE", "PARAM_NORM", 
        "MEM_VAL", "REL_VAL", "OWN_PRE", "POL_ESC_PRE",
        "PERF_PRE", "NATIVE_INV", "POST_VAL", "OWN_COMMIT",
        "IVAR_POST", "PERF_POST", "RES_GOV", "TEL_EMIT", "MET_UPD"
    ]
    
    assert orch._stages == expected

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
    assert ctx.policy_orchestrator.validate_policy_consistency() is True
