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

def test_native_binary_metadata_verification():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # Simulate loading metadata for a native binary
    binary_info = {"binary_hash": "ABC123DEF"}
    report = ctx.trust_boundary.verifier.verify_artifact("NATIVE_BINARY", binary_info)
    assert report["validation_status"] == "VERIFIED"
    assert report["artifact_type"] == "NATIVE_BINARY"
