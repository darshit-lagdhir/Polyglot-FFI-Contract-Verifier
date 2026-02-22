"""
Test: Memory Pointer Depth Validation (Prompt 19 Part 3)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, PointerDepthMismatchError
)

def _ctx():
    return EnforcementContext("FP_MEM", ContractMetadata("1", "1", "FP", 64, {}))

def test_pointer_depth_mismatch_rejected():
    ctx = _ctx()
    # declared=2 (**ptr), actual=1 (*ptr)
    with pytest.raises(PointerDepthMismatchError):
        ctx.memory_engine.validate_pointer_depth(2, 1, ctx.fingerprint)

def test_pointer_depth_match_succeeds():
    ctx = _ctx()
    ctx.memory_engine.validate_pointer_depth(1, 1, ctx.fingerprint)
    ctx.memory_engine.validate_pointer_depth(0, 0, ctx.fingerprint)
