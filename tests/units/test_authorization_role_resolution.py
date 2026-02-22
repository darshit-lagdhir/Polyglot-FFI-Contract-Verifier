import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    RuntimeRole
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_role_resolution_on_init():
    meta, fp = _meta()
    
    ctx_admin = EnforcementContext(fp, meta, role=RuntimeRole.ROLE_ADMIN)
    assert ctx_admin.authorization_manager.role == RuntimeRole.ROLE_ADMIN
    
    ctx_obs = EnforcementContext(fp, meta, role=RuntimeRole.ROLE_OBSERVER)
    assert ctx_obs.authorization_manager.role == RuntimeRole.ROLE_OBSERVER
