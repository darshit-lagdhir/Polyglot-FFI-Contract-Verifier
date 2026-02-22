"""
Test: Memory Generation Epoch Reuse (Prompt 19 Part 3)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, CanonicalPointerIdentity
)

def _ctx():
    return EnforcementContext("FP_EPOCH", ContractMetadata("1", "1", "FP", 64, {}))

def test_epoch_counter_monotonically_increases():
    ctx = _ctx()
    e1 = ctx.memory_engine.next_epoch()
    e2 = ctx.memory_engine.next_epoch()
    assert e2 > e1

def test_registration_with_different_epoch_overwrites():
    """Validates that a new epoch for a same address is accepted (conceptually representing reallocation)."""
    ctx = _ctx()
    id1 = CanonicalPointerIdentity(ctx.fingerprint, 0x1000, 1, 1, "int*")
    ctx.memory_engine.register_and_validate_alias(id1, "int*")
    
    # New epoch 2
    id2 = CanonicalPointerIdentity(ctx.fingerprint, 0x1000, 2, 1, "float*")
    # This should NOT conflict because it's a different allocation epoch
    ctx.memory_engine.register_and_validate_alias(id2, "float*")
