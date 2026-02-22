import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    RuntimeConfiguration,
    PerformanceEnvelopeViolationError
)

def test_performance_envelope_violation_halts_execution():
    """Verify that exceeding total operation count budget raises PerformanceEnvelopeViolationError."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_viol",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_perf_viol", meta)
    # Set strict threshold
    ctx.config_controller.update(RuntimeConfiguration(
        max_total_operations=50
    ))
    
    engine = ctx.performance_engine
    validator = ctx.performance_validator
    
    engine.reset()
    engine.increment("validation_steps", 60) # Over threshold
    
    with pytest.raises(PerformanceEnvelopeViolationError) as excinfo:
        validator.validate_envelope("risky_func", 123)
    
    assert "Total operations (60) exceeded limit (50)" in str(excinfo.value)

def test_performance_relational_checks_violation():
    """Verify that exceeding relational check budget raises violation."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_rel",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_perf_rel", meta)
    ctx.config_controller.update(RuntimeConfiguration(
        max_relational_checks_per_call=5
    ))
    
    engine = ctx.performance_engine
    validator = ctx.performance_validator
    
    engine.reset()
    engine.increment("relational_checks", 10)
    
    with pytest.raises(PerformanceEnvelopeViolationError) as excinfo:
        validator.validate_envelope("wide_scan", 1)
    
    assert "Relational checks (10) exceeded limit" in str(excinfo.value)
