import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_simulation_report_generation():
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    
    # Enable simulation mode
    ctx.config_controller.get().simulation_mode_enabled = True
    
    # Run simulation coordinator
    report = ctx.dry_run_coordinator.run_simulation("func_a", [1, 2], synthetic_error="ERR_SYNTHETIC")
    
    # Validate report contents
    assert report["function_name"] == "func_a"
    assert report["contract_fingerprint"] == "F1"
    assert report["validation_passed"] is False
    assert report["violation_detected"] is True
    assert report["simulated_error_code"] == "ERR_SYNTHETIC"
    assert report["simulated_policy_severity"] == "ERROR"
    
    # Validate determinism
    assert "deterministic_simulation_fingerprint" in report
    
    # Assert native side-effects bypassed logic
    # As this is a pure simulation, it should not affect active invocation count
    assert ctx.active_invocation_count == 0
