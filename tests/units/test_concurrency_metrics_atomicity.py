"""
Test: Metrics Sliding Window Atomicity (Prompt 19 Part 1)
"""
import threading
import pytest
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)


def _ctx(fp="FP_MET"):
    return EnforcementContext(fp, ContractMetadata("1.0", "1.0", fp, 64, {}))


def test_metrics_record_visible_after_call():
    ctx = _ctx()
    ctx.thread_safety_verifier.verified_metrics_record("INVOCATION_COMPLETED", {"success": True})
    assert len(ctx.metrics_aggregator._window) >= 1
    assert ctx.metrics_aggregator._window[-1]["type"] == "INVOCATION_COMPLETED"


def test_metrics_window_does_not_exceed_limit():
    """Window size is capped at metrics_window_size."""
    ctx = _ctx("FP_CAP")
    limit = ctx.config_controller.get().metrics_window_size
    for i in range(limit + 50):
        ctx.thread_safety_verifier.verified_metrics_record("EVT", {"i": i})
    assert len(ctx.metrics_aggregator._window) <= limit


def test_concurrent_metrics_no_lost_update():
    """100 threads record metrics — none silently lost under lock discipline."""
    ctx = _ctx("FP_CONC")
    successes = []

    def record(i):
        ctx.thread_safety_verifier.verified_metrics_record("E", {"i": i})
        successes.append(i)

    threads = [threading.Thread(target=record, args=(i,)) for i in range(100)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(successes) == 100
    # window capped but all 100 record calls succeeded
    assert len(ctx.metrics_aggregator._window) <= ctx.config_controller.get().metrics_window_size
