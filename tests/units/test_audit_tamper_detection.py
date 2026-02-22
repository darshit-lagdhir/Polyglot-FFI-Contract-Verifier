import pytest
import dataclasses
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    AuditIntegrityViolationError
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_audit_tamper_mismatch_detected():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    ctx.audit_manager.commit_entry("E1", "S1", "INFO")
    
    # Tamper with the chain internally
    original_entry = ctx.audit_manager._chain[0]
    # Replace entry 0 with a slightly different one
    ctx.audit_manager._chain[0] = dataclasses.replace(original_entry, event_type="MALICIOUS")
    
    with pytest.raises(AuditIntegrityViolationError):
        ctx.audit_manager.export_evidence()
