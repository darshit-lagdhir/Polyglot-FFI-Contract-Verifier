import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    OwnershipRegistry,
    InvocationState,
    InvocationOrchestrator,
    ValidationGraph,
    ValidationEngine,
    OwnershipRichRegistry
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_ownership_registry_rollback_called_on_failure():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # We'll use a subclass to track if rollback was called
    class RollbackTrackingRegistry(OwnershipRegistry):
        def __init__(self, context):
            super().__init__(context)
            self.rollback_called = False
        def rollback_staged_changes(self):
            self.rollback_called = True
            return 0
            
    ctx.registry = RollbackTrackingRegistry(ctx)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    with pytest.raises(RuntimeError):
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
        
    assert ctx.registry.rollback_called is True
