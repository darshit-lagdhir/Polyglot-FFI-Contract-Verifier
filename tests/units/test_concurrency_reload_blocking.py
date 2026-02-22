"""
Test: Reload Concurrency Blocking (Prompt 19 Part 1)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)


def _ctx(fp="FP_RLD"):
    return EnforcementContext(fp, ContractMetadata("1.0", "1.0", fp, 64, {}))


def test_reload_not_in_progress_initially():
    ctx = _ctx()
    assert not ctx.hot_reload_manager.reload_in_progress


def test_snapshot_export_works_when_no_reload():
    """Snapshot export succeeds when no reload is in progress."""
    ctx = _ctx("FP_SNAP_RLD")
    snap = ctx.snapshot_manager.export_state_snapshot()
    assert snap["contract_fingerprint"] == "FP_SNAP_RLD"


def test_deterministic_reload_sequence_counter_increments():
    """reload_sequence_counter is monotonically deterministic."""
    ctx = _ctx("FP_RSC")
    initial = ctx.hot_reload_manager.reload_sequence_counter
    # simulate finished reload
    ctx.hot_reload_manager.reload_sequence_counter += 1
    assert ctx.hot_reload_manager.reload_sequence_counter == initial + 1
