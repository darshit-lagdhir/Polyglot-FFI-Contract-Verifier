import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta(fp_val):
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={"val": fp_val})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_cross_environment_drift_detection():
    # Env 1 artifact
    meta1, fp1 = _meta(1)
    ctx1 = EnforcementContext(fp1, meta1)
    
    # Env 2 artifact (different)
    meta2, fp2 = _meta(2)
    
    # Mismatch detection logic (typically via telemetry comparison)
    assert ctx1.trust_boundary.verifier.compute_fingerprint(meta1) != \
           ctx1.trust_boundary.verifier.compute_fingerprint(meta2)
