"""
Test: Multi-Process Snapshot Determinism (Prompt 19 Part 2)
"""
import pytest
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_SNAP_DET", 64, {})

def test_snapshot_determinism_across_simulated_clones():
    """Verifies that clones from identical state produce identical snapshots."""
    ctx = EnforcementContext("FP_DET", _meta())
    
    coord = ctx.ipc_coordinator
    clone1 = ctx.process_isolation.clone_isolated_context_state()
    clone2 = ctx.process_isolation.clone_isolated_context_state()
    
    # Coordinator should find them identical (ignoring identity index)
    assert coord.validate_clone_consistency(clone1, clone2) is True

def test_snapshot_excludes_process_specific_unstable_fields():
    """Checks that exported snapshot is deterministic (no logic process index inside the snapshot itself)."""
    ctx = EnforcementContext("FP_STABLE", _meta())
    snap = ctx.snapshot_manager.export_state_snapshot()
    
    # Root snap shouldn't have ID specific fields that change per process
    assert "logical_process_index" not in snap
