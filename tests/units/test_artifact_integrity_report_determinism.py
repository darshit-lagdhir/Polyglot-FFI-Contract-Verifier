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

def test_integrity_report_is_deterministic():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    data = {"key": "val"}
    report1 = ctx.trust_boundary.verifier.verify_artifact("TEST", data)
    report2 = ctx.trust_boundary.verifier.verify_artifact("TEST", data)
    
    assert report1 == report2
    # Ensure no temporal fields
    for r in [report1, report2]:
        for key in r:
            assert "time" not in key.lower()
            assert "pid" not in key.lower()
