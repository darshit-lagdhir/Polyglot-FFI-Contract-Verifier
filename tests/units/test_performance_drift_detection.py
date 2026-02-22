import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    RegressionBaselineManager
)

def test_performance_drift_detection_via_baseline():
    """Verify that performance snapshot changes are detected as drift."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_drift",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp", meta)
    
    # 1. Create baseline
    ctx.performance_snapshot = ctx.performance_validator.generate_performance_snapshot("func", 1)
    baseline = ctx.regression_manager.generate_new_baseline_from_snapshot()
    
    # 2. Simulate drift in performance
    ctx.performance_engine.increment("validation_steps", 500)
    ctx.performance_snapshot = ctx.performance_validator.generate_performance_snapshot("func", 1)
    current_snap = ctx.snapshot_manager.export_state_snapshot()
    
    # 3. Validate against baseline
    report = ctx.regression_manager.validate_against_baseline(baseline, current_snap)
    
    assert report["drift_detected"] is True
    # Verify that performance snapshot was the cause
    assert "last_performance_snapshot" in report["detailed_diff_entries"]
