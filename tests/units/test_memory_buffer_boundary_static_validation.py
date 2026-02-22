"""
Test: Memory Buffer Boundary Static Validation (Prompt 19 Part 3)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, BufferOverflowRiskError
)

def _ctx():
    return EnforcementContext("FP_BOUNDS", ContractMetadata("1", "1", "FP", 64, {}))

def test_buffer_overflow_risk_detected():
    ctx = _ctx()
    # 100 elements, 4 bytes each = 400 bytes. max_allowed = 300.
    with pytest.raises(BufferOverflowRiskError):
        ctx.memory_engine.validate_buffer_bounds(100, 4, 300, ctx.fingerprint)

def test_buffer_within_bounds_succeeds():
    ctx = _ctx()
    # 50 elements, 4 bytes = 200 bytes. max_allowed = 300.
    ctx.memory_engine.validate_buffer_bounds(50, 4, 300, ctx.fingerprint)
