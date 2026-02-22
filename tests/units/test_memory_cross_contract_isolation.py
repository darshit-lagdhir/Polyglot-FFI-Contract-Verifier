"""
Test: Memory Cross-Contract Isolation (Prompt 19 Part 3)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, CanonicalPointerIdentity
)

def _meta(fp):
    return ContractMetadata("1", "1", fp, 64, {})

def test_memory_engine_isolation():
    """Two different contexts must have independent pointer registries."""
    ctx_a = EnforcementContext("FP_A", _meta("FP_A"))
    ctx_b = EnforcementContext("FP_B", _meta("FP_B"))
    
    id_a = CanonicalPointerIdentity("FP_A", 0x1000, 1, 1, "void*")
    ctx_a.memory_engine.register_and_validate_alias(id_a, "void*")
    
    # 0x1000 in Context B should NOT be found initially
    assert 0x1000 not in ctx_b.memory_engine._pointer_registry

def test_epoch_counter_isolation():
    ctx_a = EnforcementContext("FP_A", _meta("FP_A"))
    ctx_b = EnforcementContext("FP_B", _meta("FP_B"))
    
    ctx_a.memory_engine.next_epoch()
    assert ctx_a.memory_engine._epoch_counter == 1
    assert ctx_b.memory_engine._epoch_counter == 0
