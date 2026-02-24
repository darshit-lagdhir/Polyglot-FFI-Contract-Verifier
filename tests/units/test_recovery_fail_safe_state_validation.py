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
    SystemHealthSeverity
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_recovery_triggers_self_healing_consistency_check():
    """Verify that recovery execution triggers full system consistency validation."""
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class ConsistencyTrackingValidator:
        def __init__(self, context):
            self.context = context
            self.check_performed = False
        def perform_full_system_consistency_check(self):
            self.check_performed = True
            from modules.module_08_language_adapter.language_adapter import SystemHealthReport
            return SystemHealthReport(ctx.fingerprint, 0, [], "SYSTEM_HEALTH_OK", "fp")
            
    ctx.consistency_validator = ConsistencyTrackingValidator(ctx)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    try:
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
    except RuntimeError:
        pass
        
    assert ctx.consistency_validator.check_performed is True
