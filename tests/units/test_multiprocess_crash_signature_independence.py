"""
Test: Multi-Process Crash Signature Independence (Prompt 19 Part 2)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, CrashSnapshot
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_CRASH", 64, {})

def test_crash_signature_independence():
    """Validates that crash signatures do not contain OS-specific PID data."""
    ctx = EnforcementContext("FP_CRASH", _meta())
    
    # Manually add a "safe" crash
    ctx.crash_manager._snapshots.append(CrashSnapshot(
        signature="ERR_SAMPLE_ABORT|0x1000",
        fingerprint="FP_CRASH",
        function_name="fn1",
        invocation_idx=0,
        category="ABORT",
        metadata={}
    ))
    
    # Should pass
    assert ctx.ipc_coordinator.assert_crash_signature_pid_independent() is True

def test_crash_signature_failure_if_pid_contained():
    """Coordinator detects if PID is leaked into signature."""
    ctx = EnforcementContext("FP_CRASH_FAIL", _meta())
    from datetime import datetime
    ctx.crash_manager._snapshots.append(CrashSnapshot(
        signature="ERR_CRASH|PID=1234",
        fingerprint="FP_CRASH_FAIL",
        function_name="fn_fail",
        invocation_idx=0,
        category="CRASH",
        metadata={}
    ))
    
    # Should fail assertion
    assert ctx.ipc_coordinator.assert_crash_signature_pid_independent() is False
