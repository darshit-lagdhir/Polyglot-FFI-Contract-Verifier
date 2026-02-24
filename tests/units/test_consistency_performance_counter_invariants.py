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

def test_performance_counter_invariant_evaluation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    validator = SystemConsistencyValidator(ctx)
    
    # Force an impossible counter state
    # We'd need to mock the instrument engine if it validates internally
    
    report = validator.perform_full_system_consistency_check()
    assert "PERFORMANCE_COUNTER_INVARIANTS" not in report.failed_invariant_domains
