import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, SecurityViolationError
)

def test_monkey_patch_detection():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().monkey_patch_detection_enabled = True
    
    def original_method(): pass
    def patched_method(): pass
    
    ctx.security_manager.record_method_signature("test_mgr", original_method)
    
    # Verify original passes
    ctx.security_manager.verify_no_monkey_patch("test_mgr", original_method)
    
    # Verify patch fails
    with pytest.raises(SecurityViolationError) as excinfo:
        ctx.security_manager.verify_no_monkey_patch("test_mgr", patched_method)
    assert "Monkey-patching detected" in str(excinfo.value)
