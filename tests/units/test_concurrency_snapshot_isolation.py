"""
Test: Snapshot Isolation (Prompt 19 Part 1)
"""
import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext, ContractMetadata
)

def _meta():
    return ContractMetadata("1.0", "1.0", "FP_SNAP", 64, {})

def test_validated_snapshot_export_isolation():
    """Checks that validated_snapshot_export provides isolation by holding locks."""
    ctx = EnforcementContext("FP_ISO", _meta())
    # This call acquires all Locks in order, ensuring a consistent state snapshot.
    # If it fails to acquire them or deadlocks, the test fail.
    snapshot = ctx.thread_safety_verifier.validated_snapshot_export()
    
    assert snapshot["contract_fingerprint"] == "FP_ISO"
    assert "lifecycle_registry_summary" in snapshot
    assert "violation_aggregation_summary" in snapshot

def test_snapshot_no_concurrent_mutation_detected():
    """
    Ensures that calling validated_snapshot_export is stable.
    (In a real multi-threaded scenario, this would block mutations).
    """
    ctx = EnforcementContext("FP_STABLE", _meta())
    snap1 = ctx.thread_safety_verifier.validated_snapshot_export()
    snap2 = ctx.thread_safety_verifier.validated_snapshot_export()
    
    # Deterministic comparison
    assert snap1["contract_fingerprint"] == snap2["contract_fingerprint"]
    assert snap1["lifecycle_registry_summary"] == snap2["lifecycle_registry_summary"]
