import pytest
import sys
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ABICompatibilityError
)

def test_abi_endianness_mismatch_fails_init():
    """Verify that an endianness mismatch causes context rejection."""
    runtime_endian = sys.byteorder
    wrong_endian = "big" if runtime_endian == "little" else "little"
    
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp_endian",
        abi_bits=64 if sys.maxsize > 2**32 else 32,
        descriptors={},
        custom_metadata={"endianness": wrong_endian}
    )
    
    with pytest.raises(ABICompatibilityError) as excinfo:
        EnforcementContext("test_fp_endian", meta)
    
    assert "Endianness mismatch" in str(excinfo.value)
