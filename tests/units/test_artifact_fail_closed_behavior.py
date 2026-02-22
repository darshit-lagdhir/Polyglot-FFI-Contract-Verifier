import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ArtifactIntegrityError
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_fail_closed_on_integrity_violation():
    meta, fp = _meta()
    
    # Try to initialize with tampered metadata
    with pytest.raises(ArtifactIntegrityError):
        # We provide a metadata but the fingerprint doesn't match
        EnforcementContext("CORRUPT_FP", meta)
