"""
Test: Memory Illegal Cast Detection (Prompt 19 Part 3)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, IllegalCastError
)

def _ctx():
    return EnforcementContext("FP_CAST", ContractMetadata("1", "1", "FP", 64, {}))

def test_illegal_cast_int_to_ptr_rejected():
    ctx = _ctx()
    # int to int* direct cast without canonical wrapper check
    with pytest.raises(IllegalCastError):
        ctx.memory_engine.validate_no_illegal_cast("int", "int*", ctx.fingerprint)

def test_illegal_cast_array_to_struct_rejected():
    ctx = _ctx()
    with pytest.raises(IllegalCastError):
        ctx.memory_engine.validate_no_illegal_cast("array[u8]", "struct Foo*", ctx.fingerprint)

def test_illegal_cast_ptr_to_narrower_int_rejected():
    ctx = _ctx()
    with pytest.raises(IllegalCastError):
        ctx.memory_engine.validate_no_illegal_cast("void*", "int", ctx.fingerprint)
