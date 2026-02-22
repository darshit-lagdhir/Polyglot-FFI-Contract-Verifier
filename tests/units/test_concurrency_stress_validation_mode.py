"""
Test: Concurrency Stress Validation Mode (Prompt 19 Part 1)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, RuntimeConfiguration
)

def test_concurrency_stress_flag_persistence():
    """Validates that the stress flag is correctly stored in configuration."""
    config = RuntimeConfiguration(concurrency_stress_validation_enabled=True)
    assert config.concurrency_stress_validation_enabled is True

def test_concurrency_stress_enabled_in_context():
    """Checks that context respects the stress validation flag."""
    ctx = EnforcementContext("FP_STRESS", ContractMetadata("1", "1", "FP", 64, {}))
    ctx.config_controller.update(RuntimeConfiguration(concurrency_stress_validation_enabled=True))
    
    current_cfg = ctx.config_controller.get()
    assert current_cfg.concurrency_stress_validation_enabled is True
