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
    OwnershipRichRegistry
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_audit_chain_integrity_after_recovery():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    try:
        orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
    except RuntimeError:
        pass
        
    # Verify hash-chain integrity is preserved after recovery entry append
    ctx.audit_manager._validate_chain_integrity()
    
    # Check for RECOVERY_EVENT entry
    assert any(e.event_type == "RECOVERY_EVENT" for e in ctx.audit_manager._chain)
