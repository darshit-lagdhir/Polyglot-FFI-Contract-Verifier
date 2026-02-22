import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ContractTerminationError,
    ContractLifecycleState
)

def _meta():
    return ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="FP",
        abi_bits=64,
        descriptors={"func": None}
    )

def test_termination_blocks_invocation():
    """Verify that a terminated contract rejects new invocations."""
    ctx = EnforcementContext("FP", _meta())
    
    # Check initial state
    assert ctx.termination_manager.is_active() is True
    
    # Perform termination
    ctx.termination_manager.initiate_termination(reason="MANUAL_RETIREMENT")
    assert ctx.termination_manager.is_active() is False
    
    # Attempting to execute via orchestrator should fail
    from modules.module_08_language_adapter.language_adapter import InvocationOrchestrator, RuntimeConfiguration
    from unittest.mock import MagicMock
    orch = InvocationOrchestrator(MagicMock(), MagicMock(), RuntimeConfiguration())
    
    with pytest.raises(ContractTerminationError) as excinfo:
        orch.execute_pipeline("func", MagicMock(), [], ctx)
    assert "terminated" in str(excinfo.value)

def test_hard_reset_clears_state():
    """Verify that hard reset wipes state and returns to ACTIVE."""
    ctx = EnforcementContext("FP", _meta())
    ctx.termination_manager.initiate_termination()
    assert not ctx.termination_manager.is_active()
    
    # Set some state
    ctx.metrics_aggregator._window = [{"status": "test"}]
    
    ctx.hard_reset_coordinator.execute_hard_reset()
    assert ctx.termination_manager.is_active() is True
    assert len(ctx.metrics_aggregator._window) == 0
