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

def test_audit_entry_creation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # Init already added one entry: LIFECYCLE_INITIALIZED
    assert len(ctx.audit_manager._chain) == 1
    
    ctx.audit_manager.commit_entry("TEST_EVENT", "STAGE_X", "INFO")
    assert len(ctx.audit_manager._chain) == 2
    
    entry = ctx.audit_manager._chain[1]
    assert entry.event_type == "TEST_EVENT"
    assert entry.sequence_index == 1
    assert entry.previous_chain_fingerprint != "0"*32 # Should point to entry 0
