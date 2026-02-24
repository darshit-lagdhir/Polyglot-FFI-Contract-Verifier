import dataclasses
import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    LongRunResilienceManager,
    ContinuousOperationCertificationEngine,
    LongRunStability,
    SystemHealthSeverity
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_audit_compaction_on_ceiling_exceeded():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    resilience = LongRunResilienceManager(ctx)
    resilience.max_audit_entries = 10
    
    # Fill audit trail
    for i in range(20):
        ctx.audit_manager.commit_entry("EVENT", "STAGE", "INFO")
        
    assert len(ctx.audit_manager._chain) == 21 # Inc init
    resilience.check_resilience_ceilings()
    
    # Verify compaction occurred
    assert len(ctx.audit_manager._chain) <= 11 # 10 (half) + 1 (compaction event)
    assert any(e.event_type == "AUDIT_CHAIN_COMPACTED" for e in ctx.audit_manager._chain)

def test_long_run_drift_detection():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    cert_engine = ContinuousOperationCertificationEngine(ctx)
    
    # Simulate high recovery rate -> CRITICAL drift
    ctx.invocation_sequence_counter = 100
    ctx.recovery_orchestrator.recovery_count = 10 # 10% rate > 5% limit
    
    report = cert_engine.generate_certification_report()
    assert report.drift_classification == LongRunStability.LONG_RUN_CRITICAL.value

def test_certification_report_determinism():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    cert_engine = ContinuousOperationCertificationEngine(ctx)
    
    r1 = cert_engine.generate_certification_report()
    r2 = cert_engine.generate_certification_report()
    
    assert r1.deterministic_certification_fingerprint == r2.deterministic_certification_fingerprint

def test_fail_closed_on_critical_health():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # Trigger critical health
    ctx.audit_manager._chain[0] = dataclasses.replace(ctx.audit_manager._chain[0], entry_fingerprint="BROKEN")
    report = ctx.consistency_validator.perform_full_system_consistency_check()
    assert report.severity_classification == SystemHealthSeverity.SYSTEM_HEALTH_CRITICAL.value
    
    # Verify critical event logged
    assert any(e.event_type == "SYSTEM_HEALTH_CRITICAL" for e in ctx.audit_manager._chain)
