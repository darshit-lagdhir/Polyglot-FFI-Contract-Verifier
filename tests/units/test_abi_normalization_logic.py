import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError
)

def test_abi_normalization_alignment():
    """Verify alignment normalization logic."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_norm",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp_norm", meta)
    norm = ctx.variance_normalizer
    
    # If declared > 0, it should be respected
    assert norm.normalize_alignment(16, 8) == 16
    # If declared == 0, use default
    assert norm.normalize_alignment(0, 4) == 4

def test_abi_calling_convention_validation():
    """Verify calling convention validation."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_conv",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_fp_conv", meta)
    norm = ctx.variance_normalizer
    
    # cdecl should be supported everywhere usually
    norm.validate_calling_convention("cdecl")
    
    # invalid one should fail
    with pytest.raises(ABICompatibilityError):
        norm.validate_calling_convention("pascal_extreme_v2")
