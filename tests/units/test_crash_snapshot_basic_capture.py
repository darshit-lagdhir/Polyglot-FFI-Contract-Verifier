import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def test_crash_snapshot_generation():
    """Ensure crash forensics manager creates deterministic snapshots."""
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    ctx.crash_manager.capture_snapshot("my_func", "Sandbox", "ERR_SANDBOX_SIGSEGV")
    
    assert len(ctx.crash_manager._snapshots) == 1
    snapshot = ctx.crash_manager._snapshots[0]
    
    assert snapshot.fingerprint == "F1"
    assert snapshot.function_name == "my_func"
    assert snapshot.category == "Sandbox"
    assert snapshot.metadata["error_code"] == "ERR_SANDBOX_SIGSEGV"
    
    # Assert no timestamp is included
    assert "timestamp" not in snapshot.metadata
    
    # Assert stable formatting is computed
    assert len(snapshot.signature) == 16
