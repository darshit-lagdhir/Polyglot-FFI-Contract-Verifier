import pytest
import sys
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError
)

def test_abi_mixed_compiler_risk_fails_init():
    """Verify that a compiler family mismatch (risk) causes context rejection."""
    # Build metadata with a "wrong" compiler
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_compiler",
        abi_bits=64 if sys.maxsize > 2**32 else 32,
        descriptors={},
        custom_metadata={"compiler_family": "non_existent_compiler"}
    )
    
    with pytest.raises(ABICompatibilityError) as excinfo:
        EnforcementContext("test_fp_compiler", meta)
    
    assert "Mixed compiler risk" in str(excinfo.value)
