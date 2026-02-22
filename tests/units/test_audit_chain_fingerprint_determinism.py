import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_audit_chain_is_deterministic():
    meta, fp = _meta()
    
    ctx1 = EnforcementContext(fp, meta)
    ctx1.audit_manager.commit_entry("E1", "S1", "INFO")
    ctx1.audit_manager.commit_entry("E2", "S2", "INFO")
    
    ctx2 = EnforcementContext(fp, meta)
    ctx2.audit_manager.commit_entry("E1", "S1", "INFO")
    ctx2.audit_manager.commit_entry("E2", "S2", "INFO")
    
    assert ctx1.audit_manager.get_chain_fingerprint() == ctx2.audit_manager.get_chain_fingerprint()
