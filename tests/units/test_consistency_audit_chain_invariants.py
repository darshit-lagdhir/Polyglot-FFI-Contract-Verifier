import dataclasses
import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    SystemConsistencyValidator,
    SystemHealthSeverity
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_audit_chain_invariant_violation_detection():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    validator = SystemConsistencyValidator(ctx)
    
    # Break the audit chain by manually adding an unlinked entry
    if ctx.audit_manager._chain:
        ctx.audit_manager._chain[0] = dataclasses.replace(ctx.audit_manager._chain[0], entry_fingerprint="TAMPERED")
        
        report = validator.perform_full_system_consistency_check()
        assert report.severity_classification == SystemHealthSeverity.SYSTEM_HEALTH_CRITICAL.value
        assert "AUDIT_CHAIN_INVARIANTS" in report.failed_invariant_domains
