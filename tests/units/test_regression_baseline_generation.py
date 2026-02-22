import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RegressionBaselineManager, DriftDetectionEngine
)

def test_regression_baseline_basic_workflow():
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    
    # 1. Baseline generation
    baseline = ctx.regression_manager.generate_new_baseline_from_snapshot()
    assert baseline["baseline_schema_version"] == "1.0"
    
    # 2. Acceptance
    ctx.regression_manager.accept_new_baseline(baseline)
    
    # 3. Snapshot Generation
    snapshot = ctx.snapshot_manager.export_state_snapshot()
    
    # 4. Same snapshot against baseline - NO DRIFT
    report = ctx.regression_manager.validate_against_baseline(ctx.regression_manager._accepted_baseline, snapshot)
    
    assert report["drift_detected"] is False
    assert report["severity_summary"] == "INFO"
    
    # Modify snapshot to add feature flag drift
    snapshot["active_feature_flags"]["simulation_mode"] = True
    
    report2 = ctx.regression_manager.validate_against_baseline(ctx.regression_manager._accepted_baseline, snapshot)
    
    assert report2["drift_detected"] is True
    assert "FEATURE_FLAG_DRIFT" in report2["drift_categories"]
    assert report2["severity_summary"] == "WARNING"
