import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError,
    ContractViolationError,
    OwnershipViolationError,
    SecurityViolationError
)

def test_policy_priority_resolution():
    """Verify that the priority resolver selects the correct primary violation."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_policy",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    resolver = ctx.priority_resolver
    
    v_abi   = ABICompatibilityError("ABI fail", "fp") # 95
    v_contr = ContractViolationError("func", 0, "Viol", "fp") # ERR_CONTRACT_VIOLATION -> not in map, default 0?
    v_own   = OwnershipViolationError("func", 0, "Own", "fp") # 70
    
    # Priority map check:
    # "ERR_ABI_INCOMPATIBLE": 95
    # "ERR_OWNERSHIP_VIOLATION": 70
    
    primary = resolver.resolve_violation([v_contr, v_own, v_abi])
    assert primary == v_abi
    
    # Check security vs ABI
    v_sec = SecurityViolationError("Tamper", "fp") # 90
    primary2 = resolver.resolve_violation([v_sec, v_abi])
    assert primary2 == v_abi # 95 > 90
