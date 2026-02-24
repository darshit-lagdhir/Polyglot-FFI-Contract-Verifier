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

def test_multi_invocation_isolation():
    """Verify that failure in call A doesn't affect successful call B in the same context."""
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class SelectiveFailingEngine(ValidationEngine):
        def validate(self, graph, inputs, *args):
            if inputs and inputs[0] == "fail":
                raise RuntimeError("Controlled Failure")
            return True

    orchestrator = InvocationOrchestrator(SelectiveFailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    # 1. Success call
    orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), ["success"], ctx)
    assert ctx._invocation_state == InvocationState.INVOCATION_COMPLETED
    
    # 2. Failure call
    with pytest.raises(RuntimeError):
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), ["fail"], ctx)
    assert ctx._invocation_state == InvocationState.INVOCATION_ABORTED
    
    # 3. Success call again (Recovery ensures we can proceed)
    orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), ["success2"], ctx)
    assert ctx._invocation_state == InvocationState.INVOCATION_COMPLETED
    assert ctx.recovery_orchestrator.recovery_count == 1
