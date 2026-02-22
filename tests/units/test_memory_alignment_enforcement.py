"""
Test: Memory Alignment Enforcement (Prompt 19 Part 3)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, MisalignedPointerError
)

def _ctx():
    return EnforcementContext("FP_ALIGN", ContractMetadata("1", "1", "FP", 64, {}))

def test_misaligned_pointer_rejected():
    ctx = _ctx()
    # Address 0x1001 is NOT 4-byte aligned
    with pytest.raises(MisalignedPointerError):
        ctx.memory_engine.validate_alignment(0x1001, 4, ctx.fingerprint)

def test_aligned_pointer_succeeds():
    ctx = _ctx()
    # 0x1000 is 4-byte aligned
    ctx.memory_engine.validate_alignment(0x1000, 4, ctx.fingerprint)
    # 0x1000 is 8-byte aligned
    ctx.memory_engine.validate_alignment(0x1000, 8, ctx.fingerprint)
