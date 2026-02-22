"""
Test: Multi-Process Baseline Consistency (Prompt 19 Part 2)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_BASE", 64, {})

def test_baseline_fingerprint_identical_across_clones():
    """Ensures that the regression baseline fingerprint is identical in different logical processes."""
    ctx = EnforcementContext("FP_BASE", _meta())
    
    snap = ctx.snapshot_manager.export_state_snapshot()
    baseline = ctx.regression_manager.generate_new_baseline_from_snapshot(snap)
    fp1 = ctx.regression_manager.get_baseline_fingerprint(baseline)
    
    # Simulate process re-init
    ctx.process_isolation.post_fork_reinitialize()
    
    # Fingerprint of SAME baseline dictionary should be identical
    fp2 = ctx.regression_manager.get_baseline_fingerprint(baseline)
    
    assert fp1 == fp2
