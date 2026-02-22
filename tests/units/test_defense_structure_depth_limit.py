import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter, RuntimeConfiguration, DepthLimitExceededError
)

def test_deep_structure_rejection():
    from modules.module_08_language_adapter.language_adapter import EnforcementContext, ContractMetadata
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    # Override config directly for test
    config = ctx.config_controller.get()
    config.max_structure_depth = 3
    
    deep_input = [1, [2, [3, [4, [5]]]]]
    
    with pytest.raises(DepthLimitExceededError):
        ctx.adversarial_defense.validate_input_complexity(deep_input)

def test_shallow_structure_acceptance():
    from modules.module_08_language_adapter.language_adapter import EnforcementContext, ContractMetadata
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().max_structure_depth = 5
    
    shallow_input = [1, [2, [3]]]
    ctx.adversarial_defense.validate_input_complexity(shallow_input) # Should not raise
