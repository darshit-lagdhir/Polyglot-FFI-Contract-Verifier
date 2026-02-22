"""
Test: Lock Order Violation Detection (Prompt 19 Part 1)
"""
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata,
    DisciplinedLock, LockOrderViolationError,
    LOCK_LEVEL_CFG, LOCK_LEVEL_LIFECYCLE, LOCK_LEVEL_METRICS, LOCK_LEVEL_TELEMETRY
)


def _meta():
    return ContractMetadata("1.0", "1.0", "FP_LOCK", 64, {})


def test_lock_order_violation_lower_after_higher():
    """Acquiring lower-priority lock while higher held → LockOrderViolationError."""
    high = DisciplinedLock(LOCK_LEVEL_TELEMETRY, "TEL")
    low  = DisciplinedLock(LOCK_LEVEL_METRICS, "MET")

    with high:
        with pytest.raises(LockOrderViolationError) as exc:
            with low:
                pass
    assert "ERR_LOCK_ORDER_VIOLATION" in str(exc.value)


def test_lock_order_correct_sequence():
    """Correct ascending order does NOT raise."""
    l1 = DisciplinedLock(LOCK_LEVEL_CFG,      "CFG")
    l2 = DisciplinedLock(LOCK_LEVEL_LIFECYCLE, "LYC")
    l3 = DisciplinedLock(LOCK_LEVEL_METRICS,   "MET")
    # Should not raise
    with l1:
        with l2:
            with l3:
                pass


def test_lock_order_same_level_sibling_ok():
    """Two unrelated locks at same level on different names can coexist in sequence."""
    a = DisciplinedLock(LOCK_LEVEL_METRICS, "MET_A")
    b = DisciplinedLock(LOCK_LEVEL_METRICS, "MET_B")
    # Acquire, release, then acquire sibling — not concurrent, so no violation
    with a:
        pass
    with b:
        pass


def test_context_discipline_locks_hierarchy():
    """ConcurrencyDisciplineManager locks respect hierarchy in snapshot path."""
    ctx = EnforcementContext("FP1", _meta())
    disc = ctx.concurrency_discipline
    # lifecycle < alias < metrics: correct order must not raise
    with disc.lifecycle_lock:
        with disc.alias_lock:
            with disc.metrics_lock:
                pass


def test_context_discipline_violation_reverse():
    """Reverse order inside concurrency discipline raises."""
    ctx = EnforcementContext("FP2", _meta())
    disc = ctx.concurrency_discipline
    with disc.metrics_lock:
        with pytest.raises(LockOrderViolationError):
            with disc.lifecycle_lock:
                pass


def test_error_message_deterministic():
    """Error message contains deterministic fields, no timestamp."""
    high = DisciplinedLock(5, "L5")
    low  = DisciplinedLock(3, "L3")
    with high:
        try:
            with low:
                pass
        except LockOrderViolationError as e:
            msg = str(e)
            assert "L5" in msg or "L3" in msg
            assert "timestamp" not in msg.lower()
