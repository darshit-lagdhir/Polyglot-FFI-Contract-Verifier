import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    SystemConsistencyValidator,
    SystemHealthSeverity
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_global_health_report_generation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    validator = SystemConsistencyValidator(ctx)
    report = validator.perform_full_system_consistency_check()
    
    assert report.contract_fingerprint == fp
    assert report.total_invariant_checks > 0
    assert report.deterministic_health_fingerprint is not None
    assert isinstance(report.severity_classification, str)

def test_governance_role_invariants():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    validator = SystemConsistencyValidator(ctx)
    
    # Remove role to trigger violation
    ctx.authorization_manager.role = None
    report = validator.perform_full_system_consistency_check()
    assert "GOVERNANCE_ROLE_INVARIANTS" in report.failed_invariant_domains
    assert report.severity_classification == SystemHealthSeverity.SYSTEM_HEALTH_WARNING.value

def test_deprecation_and_artifact_invariants():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    validator = SystemConsistencyValidator(ctx)
    report = validator.perform_full_system_consistency_check()
    assert "DEPRECATION_PHASE_INVARIANTS" not in report.failed_invariant_domains
    assert "ARTIFACT_INTEGRITY_INVARIANTS" not in report.failed_invariant_domains
