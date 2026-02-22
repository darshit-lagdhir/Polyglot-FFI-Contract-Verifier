import pytest
import struct
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError
)

def test_abi_pointer_size_mismatch_fails_init():
    """Verify that a pointer size mismatch causes EnforcementContext to reject initialization."""
    runtime_ptr_bits = struct.calcsize("P") * 8
    wrong_bits = 32 if runtime_ptr_bits == 64 else 64
    
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_mismatch",
        abi_bits=wrong_bits,
        descriptors={},
        custom_metadata={}
    )
    
    with pytest.raises(ABICompatibilityError) as excinfo:
        EnforcementContext("test_fp_mismatch", meta)
    
    assert "Pointer size mismatch" in str(excinfo.value)
