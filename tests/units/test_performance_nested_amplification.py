import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def test_performance_nested_amplification_tracking():
    """Verify that nested invocation depth is captured in the performance snapshot."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_nested",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    
    # Simulate nested call
    ctx.active_invocation_count = 3
    
    snap = ctx.performance_validator.generate_performance_snapshot("nested_func", 1)
    assert snap.nested_depth_cost == 3
