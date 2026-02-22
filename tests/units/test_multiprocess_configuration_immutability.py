"""
Test: Multi-Process Configuration Immutability (Prompt 19 Part 2)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_CFG", 64, {})

def test_config_immutability_post_fork_sim():
    """Checks that configuration is preserved but conceptually isolated."""
    ctx = EnforcementContext("FP_CFG", _meta())
    ctx.config_controller.update(RuntimeConfiguration(deep_inspection=True))
    
    # Simulate fork
    ctx.process_isolation.post_fork_reinitialize()
    
    # Config should still be deep_inspection=True
    assert ctx.config_controller.get().deep_inspection is True
