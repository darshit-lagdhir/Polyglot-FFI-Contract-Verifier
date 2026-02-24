import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    InvocationOrchestrator,
    ValidationGraph,
    ValidationEngine,
    OwnershipRichRegistry,
    InvocationState
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_nested_invocation_failure_containment():
    """Verify that a failure in a nested invocation doesn't corrupt the outer context state beyond the failure."""
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class FailingEngine(ValidationEngine):
        def validate(self, graph, inputs, context, *args):
            if context.active_invocation_count > 1:
                 raise RuntimeError("Nested failure")
            return True

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    # Simulate outer invocation
    ctx.active_invocation_count = 1
    
    # Simulate inner invocation call
    inner_ctx = ctx # In real system, this would be a nested call
    inner_ctx.active_invocation_count = 2
    
    try:
        orchestrator.execute_pipeline("inner", ValidationGraph(function_name="f"), [], inner_ctx)
    except RuntimeError:
        pass
        
    # Inner context should be in ABORTED state
    assert inner_ctx._invocation_state == InvocationState.INVOCATION_ABORTED
    # Recovery count should be updated
    assert inner_ctx.recovery_orchestrator.recovery_count == 1
