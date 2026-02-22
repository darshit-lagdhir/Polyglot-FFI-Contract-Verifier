import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_nested_transaction_rollback():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    
    # Outer transaction
    ctx.transaction_coordinator.begin_transaction("INV-1")
    
    # Nested transaction
    ctx.transaction_coordinator.begin_transaction("INV-2")
    
    # Rollback should clear everything
    ctx.transaction_coordinator.rollback_transaction()
    
    assert len(ctx.transaction_coordinator._stack) == 0
    # Check trace record for rollback
    trace = ctx.context.trace_recorder.snapshot() if hasattr(ctx, 'context') else ctx.trace_recorder.snapshot()
    assert "TRANSACTION_ROLLBACK" in trace

def test_root_commit_trace():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.trace_recorder._enabled = True
    
    ctx.transaction_coordinator.begin_transaction("INV-1")
    ctx.transaction_coordinator.commit_transaction()
    
    assert "ROOT_TRANSACTION_COMMIT" in ctx.trace_recorder.snapshot()
