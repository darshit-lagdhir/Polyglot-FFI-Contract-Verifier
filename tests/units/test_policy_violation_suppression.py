import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError,
    OwnershipViolationError
)

def test_policy_violation_suppression_telemetry():
    """Verify that suppressed violations trigger telemetry."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_suppress",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    
    events = []
    def mock_emit(event_type, details, severity="ADVISORY"):
        events.append((event_type, details, severity))
    ctx.telemetry_manager.emit = mock_emit
    
    v_abi = ABICompatibilityError("ABI", "fp") # High
    v_own = OwnershipViolationError("f", 0, "O", "fp") # Lower
    
    primary = ctx.priority_resolver.resolve_violation([v_abi, v_own])
    
    # Verify telemetry
    suppress_events = [e for e in events if e[0] == "VIOLATION_SUPPRESSED"]
    assert len(suppress_events) > 0
    assert suppress_events[0][1]["primary"] == "ERR_ABI_INCOMPATIBLE"
    assert "ERR_OWNERSHIP_VIOLATION" in suppress_events[0][1]["suppressed"]
