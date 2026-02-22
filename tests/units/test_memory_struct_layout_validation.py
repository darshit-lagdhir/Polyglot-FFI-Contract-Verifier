"""
Test: Memory Struct Layout Validation (Prompt 19 Part 3)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, StructLayoutMismatchError
)

def _ctx():
    return EnforcementContext("FP_STRUCT", ContractMetadata("1", "1", "FP", 64, {}))

def test_struct_layout_mismatch_field_offset():
    ctx = _ctx()
    # (name, offset, size)
    declared = [("a", 0, 4), ("b", 4, 4)]
    # B offset is 8 instead of 4
    provided = [("a", 0, 4), ("b", 8, 4)]
    
    with pytest.raises(StructLayoutMismatchError):
        ctx.memory_engine.validate_struct_layout(declared, provided, ctx.fingerprint)

def test_struct_layout_mismatch_field_size():
    ctx = _ctx()
    declared = [("a", 0, 4)]
    provided = [("a", 0, 8)]
    
    with pytest.raises(StructLayoutMismatchError):
        ctx.memory_engine.validate_struct_layout(declared, provided, ctx.fingerprint)

def test_struct_layout_match_succeeds():
    ctx = _ctx()
    fields = [("a", 0, 4), ("b", 4, 8)]
    ctx.memory_engine.validate_struct_layout(fields, fields, ctx.fingerprint)
