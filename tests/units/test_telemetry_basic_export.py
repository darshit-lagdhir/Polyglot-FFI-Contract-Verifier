import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_telemetry_event_emission():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.telemetry_manager.emit("TEST_EVENT", {"data": 123}, "INFO")
    
    snapshot = ctx.telemetry_manager.export_snapshot()
    assert len(snapshot) == 1
    event = snapshot[0]
    assert event["event_type"] == "TEST_EVENT"
    assert event["details"] == {"data": 123}
    assert event["contract_fingerprint"] == "F1"

def test_telemetry_filtering():
    ctx = EnforcementContext("F1", ContractMetadata("F1", "1.0", {}, {}))
    ctx.config_controller.get().telemetry_filter_event_types = ["ALLOWED"]
    
    ctx.telemetry_manager.emit("ALLOWED", {"ok": True})
    ctx.telemetry_manager.emit("BLOCKED", {"bad": True})
    
    snapshot = ctx.telemetry_manager.export_snapshot()
    assert len(snapshot) == 1
    assert snapshot[0]["event_type"] == "ALLOWED"
