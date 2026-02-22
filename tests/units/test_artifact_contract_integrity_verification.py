import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ArtifactIntegrityError
)

def _meta(val=""):
    m = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="",
        abi_bits=64,
        descriptors={"val": val}
    )
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_contract_fingerprint_validated():
    """Verify that contract is accepted if fingerprint matches."""
    meta, fp = _meta("VALID")
    ctx = EnforcementContext(fp, meta)
    assert ctx.fingerprint == fp

def test_contract_integrity_failure_on_init():
    """Verify context initialization fails if metadata fingerprint doesn't match."""
    meta, fp = _meta("TAMPERED")
    
    with pytest.raises(ArtifactIntegrityError) as excinfo:
        EnforcementContext("WRONG_FP", meta)
    assert "Integrity check failed" in str(excinfo.value)
