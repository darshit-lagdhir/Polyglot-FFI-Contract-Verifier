import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter,
    EnforcementContext,
    ContractMetadata,
    InvocationState,
    InvocationOrchestrator,
    ValidationGraph,
    PipelineConfig,
    OwnershipRichRegistry,
    ValidationEngine
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_failure_triggers_recovery_and_correct_state():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # Mock validation engine to fail
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise ValueError("Failure in validation")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    graph = ValidationGraph(function_name="f")
    
    with pytest.raises(ValueError, match="Failure in validation"):
        orchestrator.execute_pipeline("f", graph, [], ctx)
        
    # Verify state transitions
    assert ctx._invocation_state == InvocationState.INVOCATION_ABORTED
    assert ctx.recovery_orchestrator.recovery_count == 1
    
    # Verify audit entry for recovery
    recovery_entries = [e for e in ctx.audit_manager._chain if e.event_type == "RECOVERY_EVENT"]
    assert len(recovery_entries) == 1
    assert recovery_entries[0].policy_stage == InvocationState.INVOCATION_VALIDATING.value
