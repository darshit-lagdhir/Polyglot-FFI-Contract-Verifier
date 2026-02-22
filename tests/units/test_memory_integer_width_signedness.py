"""
Test: Memory Integer Width & Signedness (Prompt 19 Part 3)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, IntegerWidthViolationError
)

def _ctx():
    return EnforcementContext("FP_INT", ContractMetadata("1", "1", "FP", 64, {}))

def test_integer_overflow_rejected():
    ctx = _ctx()
    # 256 for 8-bit unsigned (max 255)
    with pytest.raises(IntegerWidthViolationError):
        ctx.memory_engine.validate_integer_width(256, 8, False, ctx.fingerprint)

def test_signed_integer_underflow_rejected():
    ctx = _ctx()
    # -129 for 8-bit signed (min -128)
    with pytest.raises(IntegerWidthViolationError):
        ctx.memory_engine.validate_integer_width(-129, 8, True, ctx.fingerprint)

def test_integer_within_range_succeeds():
    ctx = _ctx()
    ctx.memory_engine.validate_integer_width(255, 8, False, ctx.fingerprint)
    ctx.memory_engine.validate_integer_width(-128, 8, True, ctx.fingerprint)
    ctx.memory_engine.validate_integer_width(127, 8, True, ctx.fingerprint)
