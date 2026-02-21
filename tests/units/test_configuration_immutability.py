import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_configuration_sealing():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    config = ctx.config_controller.get()
    
    # Initially not sealed
    assert config._sealed is False
    
    ctx.config_governance.seal_configuration()
    assert config._sealed is True

def test_multicontract_config_isolation():
    ctx1 = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx2 = EnforcementContext("F2", ContractMetadata("F2", "1.0", {}, {}))
    
    ctx1.config_controller.get().telemetry_enabled = False
    ctx2.config_controller.get().telemetry_enabled = True
    
    assert ctx1.config_controller.get().telemetry_enabled is False
    assert ctx2.config_controller.get().telemetry_enabled is True
