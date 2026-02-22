import pytest
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_snapshot_generation():
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    snapshot = ctx.snapshot_manager.export_state_snapshot()
    
    assert snapshot["snapshot_schema_version"] == "1.0"
    assert snapshot["contract_fingerprint"] == "F1"
    assert "active_pointer_count" in snapshot["lifecycle_registry_summary"]
    
    # Assert timestamp free and deterministic string logic
    s_str = ctx.snapshot_manager.export_state_snapshot_deterministic_string()
    assert "timestamp" not in s_str
    
    # Assert keys are ordered (JSON dumped)
    s2_str = json.dumps(snapshot, sort_keys=True)
    assert s_str == s2_str
