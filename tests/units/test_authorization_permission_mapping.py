import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    RuntimeRole,
    Permission,
    AuthorizationViolationError
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_observer_cannot_simulation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta, role=RuntimeRole.ROLE_OBSERVER)
    
    with pytest.raises(AuthorizationViolationError):
        ctx.authorization_manager.check_permission(Permission.ENABLE_SIMULATION)

def test_operator_can_simulation():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta, role=RuntimeRole.ROLE_OPERATOR)
    
    # Should not raise exception
    ctx.authorization_manager.check_permission(Permission.ENABLE_SIMULATION)
