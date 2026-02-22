import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_metrics_sliding_window_rollover():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().metrics_window_size = 5
    
    for i in range(10):
        ctx.metrics_aggregator.record_event("INV", {"idx": i})
        
    assert len(ctx.metrics_aggregator._window) == 5
    assert ctx.metrics_aggregator._window[-1]["details"]["idx"] == 9
    assert ctx.metrics_aggregator._window[0]["details"]["idx"] == 5

def test_anomaly_detection_trigger():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().metrics_window_size = 10
    ctx.config_controller.get().anomaly_crash_loop_threshold = 3
    
    # Emit 3 crashes
    for _ in range(3):
        ctx.metrics_aggregator.record_event("SANDBOX_CRASH", {})
        
    # Check if anomaly was emitted to telemetry
    snapshot = ctx.telemetry_manager.export_snapshot()
    assert any(e["event_type"] == "CRASH_LOOP_DETECTED" for e in snapshot)
