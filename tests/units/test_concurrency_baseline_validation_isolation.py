"""
Test: Baseline Validation Isolation (Prompt 19 Part 1)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_BASE", 64, {})

def test_baseline_validation_operates_on_snapshot_copy():
    """
    Ensures baseline validation uses the snapshot mechanism which 
    operates on a disconnected data structure (isolation).
    """
    ctx = EnforcementContext("FP_VALID", _meta())
    
    # 1. Generate snapshot (isolated)
    snapshot = ctx.snapshot_manager.export_state_snapshot()
    
    # 2. Generate baseline
    baseline = ctx.regression_manager.generate_new_baseline_from_snapshot(snapshot)
    
    # 3. Validate against itself
    report = ctx.regression_manager.validate_against_baseline(baseline, snapshot)
    
    assert report["drift_detected"] is False
    assert report["baseline_fingerprint"] == report["current_snapshot_fingerprint"]
