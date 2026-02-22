"""
Test: Deterministic Concurrency Behavior (Prompt 19 Part 1)
"""
import pytest
import threading
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, DeadlockRiskDetectedError
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_DET", 64, {})

def test_deadlock_guard_trigger():
    """Checks that the deadlock guard (op counter) raises error upon threshold exceed."""
    ctx = EnforcementContext("FP_DEADLOCK", _meta())
    # Use a small max_hold_ops for testing
    from modules.module_08_language_adapter.language_adapter import DisciplinedLock, LOCK_LEVEL_METRICS
    
    lock = DisciplinedLock(LOCK_LEVEL_METRICS, "DET_LOCK", max_hold_ops=5)
    
    with lock:
        # 1 to 5 ops OK
        for _ in range(5):
            lock.tick_op("FP_DEADLOCK")
        
        # 6th op should trigger
        with pytest.raises(DeadlockRiskDetectedError):
            lock.tick_op("FP_DEADLOCK")

def test_deterministic_lock_stack_isolation():
    """Ensures each thread has its own independent lock stack (deterministic isolation)."""
    from modules.module_08_language_adapter.language_adapter import DisciplinedLock, LOCK_LEVEL_CFG
    
    l1 = DisciplinedLock(LOCK_LEVEL_CFG, "L1")
    
    def thread_func():
        # Stack should be empty in new thread
        assert len(DisciplinedLock._stack()) == 0
        with l1:
            assert len(DisciplinedLock._stack()) == 1
        assert len(DisciplinedLock._stack()) == 0

    threads = [threading.Thread(target=thread_func) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
