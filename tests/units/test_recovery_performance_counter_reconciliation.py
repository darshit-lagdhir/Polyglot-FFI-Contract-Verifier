import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    PerformanceContractValidator,
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

def test_performance_counter_reconciliation_on_failure():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class ReconciliationTrackingValidator(PerformanceContractValidator):
        def __init__(self, context):
            super().__init__(context)
            self.reconciled = False
        def rollback_invocation_counters(self):
            self.reconciled = True
            
    ctx.performance_validator = ReconciliationTrackingValidator(ctx)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    with pytest.raises(RuntimeError):
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
        
    assert ctx.performance_validator.reconciled is True
