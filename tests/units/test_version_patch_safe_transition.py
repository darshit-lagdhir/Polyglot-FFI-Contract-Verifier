import pytest
import hashlib
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    VersionChangeType,
    ContractVersionTransitionError
)

def _meta(ver="1.0.0", synthesis="1.0", fp="FP"):
    return ContractMetadata(
        schema_version="1.0",
        synthesis_version=synthesis,
        fingerprint=fp,
        abi_bits=64,
        descriptors={},
        semantic_version=ver
    )

def test_version_patch_safe_transition():
    """Verify that same-version or patch-level transitions are auto-accepted."""
    ctx = EnforcementContext("FP1", _meta("1.0.0"))
    old_meta = _meta("1.0.0")
    new_meta = _meta("1.0.0") # Identical
    
    report = ctx.transition_validator.validate_transition(old_meta, new_meta)
    assert report["compatibility_status"] == "ACCEPTED"
    assert report["change_classification"] == "PATCH_SAFE"

def test_version_minor_extension_transition():
    """Verify additive changes are accepted if override provided or no baseline."""
    ctx = EnforcementContext("FP1", _meta("1.0.0"))
    old_meta = _meta("1.0.0")
    # Minor extension: add a descriptor
    new_meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="FP2",
        abi_bits=64,
        descriptors={"new_func": None},
        semantic_version="1.1.0"
    )
    
    # No baseline set yet, so should be accepted
    report = ctx.transition_validator.validate_transition(old_meta, new_meta)
    assert report["change_classification"] == "MINOR_EXTENSION"
    assert report["compatibility_status"] == "ACCEPTED"
