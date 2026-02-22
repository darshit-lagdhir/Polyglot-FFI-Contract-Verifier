import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ArtifactIntegrityError
)

def _meta():
    # Use a real fingerprint that matches meta for init to succeed
    import hashlib, json
    from dataclasses import asdict
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_baseline_integrity_check():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    baseline_data = {"baseline": "data"}
    valid_fp = ctx.trust_boundary.verifier.compute_fingerprint(baseline_data)
    
    # Successful validation
    report = ctx.trust_boundary.verifier.verify_artifact("BASELINE", baseline_data, valid_fp)
    assert report["validation_status"] == "VERIFIED"
    
    # Failed validation
    with pytest.raises(ArtifactIntegrityError):
        ctx.trust_boundary.verifier.verify_artifact("BASELINE", baseline_data, "WRONG_FP")
