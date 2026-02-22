import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, SecurityViolationError, RuntimeConfiguration
)

def test_reload_loop_prevention():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    config = ctx.config_controller.get()
    config.min_reload_interval_invocations = 100
    
    # First reload at counter 0
    ctx.hot_reload_manager.perform_reload(ctx.metadata, lambda: None)
    
    # Attempt rapid second reload (invocation counter hasn't moved 100 steps)
    ctx.invocation_sequence_counter = 10 # only 10 steps
    with pytest.raises(SecurityViolationError) as excinfo:
        ctx.hot_reload_manager.perform_reload(ctx.metadata, lambda: None)
    assert "Rapid reload loop detected" in str(excinfo.value)

def test_reload_allowed_after_interval():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    config = ctx.config_controller.get()
    config.min_reload_interval_invocations = 100
    
    ctx.hot_reload_manager.perform_reload(ctx.metadata, lambda: None)
    
    # Counter moves 101 steps
    ctx.invocation_sequence_counter = 101
    ctx.hot_reload_manager.perform_reload(ctx.metadata, lambda: None) # Should pass
