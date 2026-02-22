import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    DeprecationPhase,
    DeprecationViolationError
)

def _meta_with_dep(feature_id, phase):
    return ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="FP",
        abi_bits=64,
        descriptors={feature_id: None},
        deprecated_features=[{"id": feature_id, "phase": phase}]
    )

def test_deprecation_warning_phase():
    """Verify that WARNING phase emits telemetry but doesn't block."""
    ctx = EnforcementContext("FP", _meta_with_dep("old_func", "WARNING"))
    
    events = []
    def mock_emit(event_type, details, severity="ADVISORY"):
        events.append((event_type, details))
    ctx.telemetry_manager.emit = mock_emit
    
    # Usage check
    ctx.deprecation_manager.check_feature_usage("old_func")
    
    warning_events = [e for e in events if e[0] == "DEPRECATION_WARNING"]
    assert len(warning_events) == 1
    assert warning_events[0][1]["feature"] == "old_func"

def test_deprecation_enforced_blocked():
    """Verify that ENFORCED phase blocks feature usage."""
    ctx = EnforcementContext("FP", _meta_with_dep("old_func", "ENFORCED"))
    
    with pytest.raises(DeprecationViolationError) as excinfo:
        ctx.deprecation_manager.check_feature_usage("old_func")
    assert "enforced-blocked" in str(excinfo.value)

def test_deprecation_sunset_blocked():
    """Verify that SUNSET phase blocks feature usage with specific error."""
    ctx = EnforcementContext("FP", _meta_with_dep("dead_func", "SUNSET"))
    
    with pytest.raises(DeprecationViolationError) as excinfo:
        ctx.deprecation_manager.check_feature_usage("dead_func")
    assert "sunset and removed" in str(excinfo.value)
