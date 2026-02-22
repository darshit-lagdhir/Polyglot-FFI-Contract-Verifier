import pytest
import hashlib
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata
)

def _meta(ver, synthesis="1.0", fp="FP"):
    return ContractMetadata(
        schema_version="1.0",
        synthesis_version=synthesis,
        fingerprint=fp,
        abi_bits=64,
        descriptors={},
        semantic_version=ver
    )

def test_version_deterministic_transition_report():
    """Verify that version transition reports are stable and include no timestamp."""
    ctx = EnforcementContext("FP1", _meta("1.0.0"))
    old_meta = _meta("1.0.0", fp="FP_OLD")
    new_meta = _meta("1.1.0", fp="FP_NEW")
    
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
    meta1 = _meta("1.0.0", fp="FP1")
    meta2 = _meta("1.0.0", fp="FP2")
    ctx1 = EnforcementContext("FP1", meta1)
    ctx2 = EnforcementContext("FP2", meta2)
    
    ctx1.termination_manager.initiate_termination()
    
    assert not ctx1.termination_manager.is_active()
    assert ctx2.termination_manager.is_active() is True
