import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    RuntimeConfiguration,
    PerformanceEnvelopeViolationError,
    TelemetryEvent
)

def test_performance_relational_blowup_telemetry():
    """Verify that high relational count triggers blowup telemetry."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_blowup",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    
    # We need to capture telemetry
    events = []
    def mock_emit(event_type, details, severity="ADVISORY"):
        events.append((event_type, details, severity))
    
    ctx.telemetry_manager.emit = mock_emit
    
    engine = ctx.performance_engine
    validator = ctx.performance_validator
    
    engine.reset()
    engine.increment("relational_checks", 150) # Above blowup threshold (100)
    
    # We might still pass the envelope if limit is 0 or high
    validator.validate_envelope("big_join", 1)
    
    # Check for blowup event
    blowup_events = [e for e in events if e[0] == "RELATIONAL_BLOWUP_DETECTED"]
    assert len(blowup_events) > 0
    assert blowup_events[0][1]["count"] == 150
