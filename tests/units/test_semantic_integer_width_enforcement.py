import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, ContractViolationError
)

def test_strict_integer_width_rejection():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().strict_integer_width = True
    
    # 8-bit signed range: -128 to 127
    with pytest.raises(ContractViolationError) as excinfo:
        ctx.semantic_coordinator.normalize_integer(200, 8)
    assert "Integer overflow for width 8" in str(excinfo.value)

def test_implicit_type_rejection():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().strict_integer_width = True
    
    # Reject float-to-int
    with pytest.raises(ContractViolationError) as excinfo:
        ctx.semantic_coordinator.normalize_integer(10.5, 32)
    assert "Implicit float-to-int conversion rejected" in str(excinfo.value)
    
    # Reject bool-to-int
    with pytest.raises(ContractViolationError) as excinfo:
        ctx.semantic_coordinator.normalize_integer(True, 32)
    assert "Bool as integer rejected" in str(excinfo.value)
