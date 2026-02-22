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

def test_snapshot_integrity():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    snapshot = {"state": "full"}
    valid_fp = ctx.trust_boundary.verifier.compute_fingerprint(snapshot)
    
    report = ctx.trust_boundary.verifier.verify_artifact("SNAPSHOT", snapshot, valid_fp)
    assert report["validation_status"] == "VERIFIED"
