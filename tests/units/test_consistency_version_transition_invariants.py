import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    SystemConsistencyValidator
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_version_transition_invariant_evaluation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    validator = SystemConsistencyValidator(ctx)
    report = validator.perform_full_system_consistency_check()
    assert "VERSION_TRANSITION_INVARIANTS" not in report.failed_invariant_domains
