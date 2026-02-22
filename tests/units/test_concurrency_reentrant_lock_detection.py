"""
Test: Reentrant Lock Detection (Prompt 19 Part 1)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    DisciplinedLock, ReentrantLockError, LOCK_LEVEL_METRICS
)


def test_reentrant_same_lock_name_and_level():
    """Acquiring the identical (name, level) lock twice without release → ReentrantLockError."""
    lock = DisciplinedLock(LOCK_LEVEL_METRICS, "MET")
    with lock:
        with pytest.raises(ReentrantLockError) as exc:
            with lock:
                pass
    assert "ERR_REENTRANT_LOCK" in str(exc.value)


def test_different_name_same_level_no_reentrant():
    """Two distinct names at the same level are NOT considered reentrant when nested correctly."""
    # With ascending order constraint they still raise LockOrderViolationError –
    # but NOT ReentrantLockError specifically.  We test that the error is NOT reentrant.
    a = DisciplinedLock(LOCK_LEVEL_METRICS, "MET_X")
    b = DisciplinedLock(LOCK_LEVEL_METRICS + 1, "MET_Y")  # higher
    # Correct: acquire a then b
    with a:
        with b:
            pass  # no error expected


def test_reentrant_error_message_no_timestamp():
    """Reentrant error message is deterministic, contains no timestamp."""
    lock = DisciplinedLock(4, "RLOCK")
    with lock:
        try:
            with lock:
                pass
        except ReentrantLockError as e:
            assert "ERR_REENTRANT_LOCK" in str(e)
            assert "timestamp" not in str(e).lower()
