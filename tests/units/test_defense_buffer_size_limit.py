import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, SecurityViolationError
)

def test_buffer_size_limit():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().max_buffer_size = 1000
    
    # Valid size
    ctx.adversarial_defense.validate_buffer_size(500)
    
    # Invalid size
    with pytest.raises(SecurityViolationError) as excinfo:
        ctx.adversarial_defense.validate_buffer_size(2000)
    assert "Buffer size 2000 exceeds limit" in str(excinfo.value)
