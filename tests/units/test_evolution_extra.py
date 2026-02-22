import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta(ver, synthesis="1.0"):
    m = ContractMetadata(
        schema_version="1.0",
        synthesis_version=synthesis,
        fingerprint="",
        abi_bits=64,
        descriptors={},
        semantic_version=ver
    )
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_version_deterministic_transition_report():
    """Verify that version transition reports are stable and include no timestamp."""
    meta, fp = _meta("1.0.0")
    ctx = EnforcementContext(fp, meta)
    
    old_meta, _ = _meta("1.0.0")
    new_meta, _ = _meta("1.1.0")
    
    report1 = ctx.transition_validator.validate_transition(old_meta, new_meta)
    report2 = ctx.transition_validator.validate_transition(old_meta, new_meta)
    
    assert report1 == report2
    assert "deterministic_transition_fingerprint" in report1
    # Ensure no temporal leakage
    for key in report1:
        assert "time" not in key.lower()
        assert "date" not in key.lower()

def test_termination_multicontract_isolation():
    """Verify that terminating one contract doesn't affect another."""
    meta1, fp1 = _meta("1.0.0")
    meta2, fp2 = _meta("2.0.0")
    ctx1 = EnforcementContext(fp1, meta1)
    ctx2 = EnforcementContext(fp2, meta2)
    
    ctx1.termination_manager.initiate_termination()
    
    assert not ctx1.termination_manager.is_active()
    assert ctx2.termination_manager.is_active() is True
