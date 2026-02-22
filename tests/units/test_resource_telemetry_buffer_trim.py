import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_telemetry_buffer_trimming():
    """Ensure resource governor enforces max telemetry entries bounded retention."""
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    ctx.config_controller.get().max_telemetry_entries = 5
    
    # Emit 10 events, caps enforced
    for i in range(10):
        ctx.telemetry_manager.emit("INV", {"idx": i})
        ctx.resource_governor.enforce_caps()
        
    buffer = ctx.telemetry_manager._buffer
    
    # Assert buffer size is bounded correctly (accounting for warnings)
    assert len(buffer) <= 7
    
    # Assert there are actual telemetry elements inside
    assert len([b for b in buffer if b.event_type == "INV"]) > 0

def test_crash_snapshot_trimming():
    """Ensure resource governor enforces max crash snapshots bounded retention."""
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    ctx.config_controller.get().max_crash_snapshots = 3
    
    # Capture 5 crashes
    for i in range(5):
        ctx.crash_manager.capture_snapshot(f"my_func_{i}", "Sandbox", "ERR")
        ctx.resource_governor.enforce_caps()
        
    snapshots = ctx.crash_manager._snapshots
    
    # bounded limit
    assert len(snapshots) == 3
    assert snapshots[0].function_name == "my_func_2"
    assert snapshots[-1].function_name == "my_func_4"
