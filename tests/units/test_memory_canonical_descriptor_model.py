"""
Test: Memory Canonical Descriptor Model (Prompt 19 Part 3)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, CanonicalMemoryDescriptor
)

def _ctx():
    return EnforcementContext("FP_DESC", ContractMetadata("1", "1", "FP", 64, {}))

def test_canonical_descriptor_creation():
    ctx = _ctx()
    # base, size, align, type_sig, mutable, owner, depth
    desc = ctx.memory_engine.build_canonical_descriptor(
        0x1000, 4, 4, "u32*", True, "caller", 1
    )
    
    assert isinstance(desc, CanonicalMemoryDescriptor)
    assert desc.base_address == 0x1000
    assert desc.allocation_epoch > 0

def test_pointer_canonicalizer_creates_descriptor():
    ctx = _ctx()
    # integer value (address) passed as int*
    desc = ctx.pointer_canonicalizer.canonicalize(0x2000, "int*")
    
    assert desc.base_address == 0x2000
    assert desc.pointer_depth == 1
    assert desc.type_signature == "int*"
