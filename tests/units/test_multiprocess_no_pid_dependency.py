"""
Test: No PID Dependency (Prompt 19 Part 2)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_PID", 64, {})

def test_snapshot_no_pid_dependency():
    """Checks that a standard snapshot does not leak the OS PID."""
    ctx = EnforcementContext("FP_001", _meta())
    snap = ctx.snapshot_manager.export_state_snapshot()
    
    assert ctx.ipc_coordinator.assert_no_pid_in_snapshot(snap) is True

def test_deteminstic_logical_process_index():
    """Confirms logical process index is present and numeric."""
    ctx = EnforcementContext("FP_PID_2", _meta())
    idx = ctx.process_isolation.identity.logical_process_index
    assert isinstance(idx, int)
    assert idx > 0
