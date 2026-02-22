"""
Test: Multi-Process Sandbox Supervision (Prompt 19 Part 2)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_SAND", 64, {})

def test_sandbox_supervision_reinitialization():
    """Validates that sandbox manager state (like restart counters) can be reset effectively."""
    ctx = EnforcementContext("FP_SAND", _meta())
    
    # Simulate a crash happened in parent (conceptually)
    ctx.metrics_aggregator.record_event("SANDBOX_CRASH", {})
    
    # Re-init process context
    ctx.process_isolation.post_fork_reinitialize()
    
    # Metrics should be fresh
    assert len(ctx.metrics_aggregator._window) == 0
