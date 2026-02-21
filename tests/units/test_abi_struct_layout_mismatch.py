import pytest
import ctypes
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, AbiLayoutMismatchError
)

class ValidStruct(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int32), ("b", ctypes.c_int32)]

class InvalidStruct(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int32), ("padding", ctypes.c_int32), ("b", ctypes.c_int32)]

def test_abi_fingerprint_mismatch():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().abi_validation_enabled = True
    
    expected = ctx.abi_validator.compute_struct_fingerprint(ValidStruct)
    
    # Should pass for ValidStruct
    ctx.abi_validator.validate_layout("TestStruct", ValidStruct, expected)
    
    # Should fail for InvalidStruct
    with pytest.raises(AbiLayoutMismatchError) as excinfo:
        ctx.abi_validator.validate_layout("TestStruct", InvalidStruct, expected)
    assert "ABI fingerprint mismatch" in str(excinfo.value)
