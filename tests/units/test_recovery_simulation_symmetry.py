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
    InvocationState,
    DryRunCoordinator
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_simulation_recovery_symmetry():
    """Verify that simulation mode follows the same recovery flow as live mode."""
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Simulation Failure")

    # DryRunCoordinator uses the internal execute_pipeline with a dry_run config
    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.dry_run = True
    orchestrator.config.enable_pre_validation = True
    
    with pytest.raises(RuntimeError):
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
        
    assert ctx._invocation_state == InvocationState.INVOCATION_ABORTED
    assert ctx.recovery_orchestrator.recovery_count == 1
    assert any(e.event_type == "RECOVERY_EVENT" for e in ctx.audit_manager._chain)
