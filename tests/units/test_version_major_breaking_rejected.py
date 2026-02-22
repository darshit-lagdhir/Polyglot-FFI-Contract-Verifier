import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ContractVersionTransitionError
)

def _meta(ver="1.0.0", descriptors=None):
    if descriptors is None: descriptors = {}
    return ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="FP",
        abi_bits=64,
        descriptors=descriptors,
        semantic_version=ver
    )

def test_version_major_breaking_rejected():
    """Verify that major version increments are rejected without override."""
    ctx = EnforcementContext("FP1", _meta("1.0.0"))
    old_meta = _meta("1.0.0")
    new_meta = _meta("2.0.0")
    
    with pytest.raises(ContractVersionTransitionError) as excinfo:
        ctx.transition_validator.validate_transition(old_meta, new_meta)
    assert "MAJOR_BREAKING" in str(excinfo.value)
    
    # Check with override
    report = ctx.transition_validator.validate_transition(old_meta, new_meta, override=True)
    assert report["compatibility_status"] == "ACCEPTED"

def test_version_abi_breaking_rejected():
    """Verify that ABI bitness change is rejected."""
    old_meta = _meta("1.0.0")
    # Change ABI bits
    new_meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="FP",
        abi_bits=32, # Changed from 64
        descriptors={},
        semantic_version="1.0.1"
    )
    ctx = EnforcementContext("FP1", old_meta)
    
    with pytest.raises(ContractVersionTransitionError) as excinfo:
        ctx.transition_validator.validate_transition(old_meta, new_meta)
    assert "ABI_BREAKING" in str(excinfo.value)
