import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, PerformanceProfilingRecord, InternalInvariantViolationError
)

def test_profiling_consistency_invariant():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().invariant_checks_enabled = True
    
    # Mock some profiling data
    record = PerformanceProfilingRecord()
    record.invocation_count = 10
    record.minimal_path_invocations = 15 # Inconsistency: path > total
    
    ctx.profiling_manager._registry["test_func"] = record
    
    with pytest.raises(InternalInvariantViolationError) as excinfo:
        ctx.invariant_manager.assert_all_invariants()
    assert "Profiling inconsistency" in str(excinfo.value)
