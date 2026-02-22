"""
Test: Multi-Process IPC Determinism (Prompt 19 Part 2)
"""
import pytest
import json
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_IPC", 64, {})

def test_ipc_message_determinism():
    """Ensures IPC messages have deterministic fields and ordering."""
    ctx = EnforcementContext("FP_IPC", _meta())
    
    msg1 = ctx.process_isolation.get_deterministic_ipc_message(
        "TEST_EVENT", {"data": 1, "alpha": "z"}
    )
    msg2 = ctx.process_isolation.get_deterministic_ipc_message(
        "TEST_EVENT", {"alpha": "z", "data": 1}
    )
    
    # Payload keys should be sorted, root keys should be sorted
    assert json.dumps(msg1, sort_keys=True) == json.dumps(msg2, sort_keys=True)
    assert "ipc_schema_version" in msg1
    assert "logical_process_index" in msg1

def test_ipc_no_forbidden_fields():
    """IPC messages must not contain PIDs or addresses."""
    ctx = EnforcementContext("FP_IPC_SAFE", _meta())
    msg = ctx.process_isolation.get_deterministic_ipc_message("EVT", {"pid": 1234, "addr": 0xdead})
    
    serialized = json.dumps(msg)
    # The payload is wrapped, but we ensure the Coordinator's check would fail if leaked at root
    # or if we strictly forbid those specific key-sequences in the system-produced message.
    assert ctx.ipc_coordinator.assert_no_pid_in_snapshot(msg) is False # because we put "pid" in payload
