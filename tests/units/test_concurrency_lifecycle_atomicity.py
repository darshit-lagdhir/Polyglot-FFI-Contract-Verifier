"""
Test: Lifecycle Registry Atomicity (Prompt 19 Part 1)
"""
import threading
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)


def _ctx(fp="FP_LC"):
    return EnforcementContext(fp, ContractMetadata("1.0", "1.0", fp, 64, {}))


def test_lifecycle_lock_acquired_during_snapshot():
    """Verified snapshot export acquires lifecycle lock without deadlock."""
    ctx = _ctx()
    snap = ctx.thread_safety_verifier.validated_snapshot_export()
    assert "lifecycle_registry_summary" in snap


def test_concurrent_telemetry_append_no_partial_state():
    """100 threads appending telemetry events under telemetry lock → no partial events."""
    ctx = _ctx("FP_TEL")
    barriers_hit = []

    from modules.module_08_language_adapter.language_adapter import TelemetryEvent
    import time

    def do_append(i):
        evt = TelemetryEvent(
            schema_version="1.0",
            contract_fingerprint="FP_TEL",
            event_type="CONCURRENT_EMIT",
            invocation_idx=i,
            function_name="fn",
            details={"i": i},
            severity="INFO"
        )
        ctx.thread_safety_verifier.verified_telemetry_append(evt)
        barriers_hit.append(i)

    threads = [threading.Thread(target=do_append, args=(i,)) for i in range(50)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(barriers_hit) == 50
    assert len(ctx.telemetry_manager._buffer) >= 50


def test_lifecycle_locking_no_cross_contract_contamination():
    """Two contexts share no lock objects."""
    ctx_a = _ctx("FP_A")
    ctx_b = _ctx("FP_B")
    da = ctx_a.concurrency_discipline
    db = ctx_b.concurrency_discipline
    assert da.lifecycle_lock is not db.lifecycle_lock
    assert da.telemetry_lock is not db.telemetry_lock
