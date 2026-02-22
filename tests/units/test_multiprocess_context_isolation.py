"""
Test: Multi-Process Context Isolation (Prompt 19 Part 2)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_PROC", 64, {})

def test_post_fork_reinitialization_isolation():
    """Checks that post_fork_reinitialize generates a new identity and clears buffers."""
    ctx = EnforcementContext("FP_FORK", _meta())
    
    # 1. Add some state
    ctx.telemetry_manager._buffer.append({"event": "parent"})
    initial_identity = ctx.process_isolation.identity.logical_process_index
    
    # 2. Simulate Fork/Reinit
    ctx.process_isolation.post_fork_reinitialize()
    
    # 3. Verify Isolation
    assert len(ctx.telemetry_manager._buffer) == 0
    assert ctx.process_isolation.identity.logical_process_index != initial_identity
    assert ctx.process_isolation.identity.contract_fingerprint == "FP_FORK"

def test_logical_process_index_uniqueness():
    """Ensures each context starts with a unique logical process index."""
    ctx1 = EnforcementContext("FP1", _meta())
    ctx2 = EnforcementContext("FP2", _meta())
    
    assert ctx1.process_isolation.identity.logical_process_index != ctx2.process_isolation.identity.logical_process_index
