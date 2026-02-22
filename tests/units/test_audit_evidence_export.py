import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_evidence_export_is_deterministic():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    ctx.audit_manager.commit_entry("EVENT_1", "STAGE_1", "INFO")
    
    export1 = ctx.evidence_exporter.generate_compliance_bundle()
    export2 = ctx.evidence_exporter.generate_compliance_bundle()
    
    assert export1 == export2
    assert "audit_trail" in export1
    assert "chain_fingerprint" in export1
    assert export1["chain_fingerprint"] == ctx.audit_manager.get_chain_fingerprint()
