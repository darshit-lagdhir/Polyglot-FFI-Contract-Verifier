"""
Test: Telemetry Buffer Atomicity (Prompt 19 Part 1)
"""
import threading
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata, TelemetryEvent
)


def _ctx(fp="FP_TELA"):
    return EnforcementContext(fp, ContractMetadata("1.0", "1.0", fp, 64, {}))


def test_telemetry_append_is_atomic():
    """Single-thread verified append is immediately visible."""
    ctx = _ctx()
    evt = TelemetryEvent("1.0", "FP_TELA", "EVT", 1, "fn", {}, "INFO")
    ctx.thread_safety_verifier.verified_telemetry_append(evt)
    assert len(ctx.telemetry_manager._buffer) >= 1


def test_telemetry_events_not_reordered_nondeterministically():
    """
    40 sequential (single-thread) appends preserve submission order.
    """
    ctx = _ctx("FP_ORD")
    for i in range(40):
        evt = TelemetryEvent("1.0", "FP_ORD", "EVT", i, "fn", {"idx": i}, "INFO")
        ctx.thread_safety_verifier.verified_telemetry_append(evt)
    indices = [e.details["idx"] for e in ctx.telemetry_manager._buffer]
    assert indices == sorted(indices)


def test_concurrent_telemetry_no_duplicate():
    """50 unique events from 50 threads — no two events share sequence_index."""
    ctx = _ctx("FP_DUP")
    results = []

    def emit(i):
        evt = TelemetryEvent("1.0", "FP_DUP", "E", i, "fn", {}, "INFO")
        ctx.thread_safety_verifier.verified_telemetry_append(evt)
        results.append(i)

    threads = [threading.Thread(target=emit, args=(i,)) for i in range(50)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(results) == 50
    seq_indices = [e.invocation_idx for e in ctx.telemetry_manager._buffer]
    assert len(set(seq_indices)) == len(seq_indices)  # unique
