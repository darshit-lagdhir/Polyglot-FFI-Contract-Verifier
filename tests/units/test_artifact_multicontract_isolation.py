import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta(name):
    import hashlib, json
    # Unique name makes unique fingerprint
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={"n": name})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_multicontract_integrity_isolation():
    meta1, fp1 = _meta("C1")
    meta2, fp2 = _meta("C2")
    
    ctx1 = EnforcementContext(fp1, meta1)
    ctx2 = EnforcementContext(fp2, meta2)
    
    ctx1.trust_boundary.seal_configuration({"config": 1})
    ctx2.trust_boundary.seal_configuration({"config": 2})
    
    # Verify they don't share seals
    assert ctx1.trust_boundary._sealed_config_fp != ctx2.trust_boundary._sealed_config_fp
