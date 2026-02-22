"""
Test: Memory Alias Detection (Prompt 19 Part 3)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, CanonicalPointerIdentity, MemoryAliasConflictError
)

def _ctx():
    return EnforcementContext("FP_ALIAS", ContractMetadata("1", "1", "FP", 64, {}))

def test_memory_alias_conflict():
    """Rejected if same address is registered with a different type signature in the same epoch."""
    ctx = _ctx()
    
    id1 = CanonicalPointerIdentity(ctx.fingerprint, 0x1000, 1, 1, "int*")
    ctx.memory_engine.register_and_validate_alias(id1, "int*")
    
    # Conflict: 0x1000 as float*
    id2 = CanonicalPointerIdentity(ctx.fingerprint, 0x1000, 1, 1, "float*")
    with pytest.raises(MemoryAliasConflictError):
        ctx.memory_engine.register_and_validate_alias(id2, "float*")

def test_memory_alias_ok_if_same_type():
    ctx = _ctx()
    id1 = CanonicalPointerIdentity(ctx.fingerprint, 0x1000, 1, 1, "int*")
    ctx.memory_engine.register_and_validate_alias(id1, "int*")
    ctx.memory_engine.register_and_validate_alias(id1, "int*") # Same is OK
