import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    LanguageAdapter,
    ContractMetadata,
    RuntimeRole,
    AuthorizationViolationError,
    EnforcementContext,
    MultiContractContextManager
)

def _meta():
    m = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="",
        abi_bits=64,
        descriptors={"f": "()" }
    )
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_simulation_blocked_for_observer():
    meta, fp = _meta()
    adapter = LanguageAdapter()
    
    # Ensure MultiContractContextManager is clean (or at least doesn't have our fp)
    mgr = MultiContractContextManager.get_instance()
    with mgr._context_lock:
        if fp in mgr._contexts:
            del mgr._contexts[fp]
            
    # Use the manager to register the context with the right role
    ctx = mgr.register_context(fp, meta, role=RuntimeRole.ROLE_OBSERVER)
    
    # Enable simulation mode on that context
    ctx.config_controller.get().simulation_mode_enabled = True
    
    with pytest.raises(AuthorizationViolationError):
        adapter.validate_invocation("f", [], fp)
