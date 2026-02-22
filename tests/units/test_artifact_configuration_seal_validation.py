import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    ArtifactIntegrityError
)

def _meta():
    import hashlib, json
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m); fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_configuration_seal_prevents_tampering():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    # Seal the configuration (already done in __init__)
    config_obj = ctx.config_controller.get()
    config_data = {k: v for k, v in vars(config_obj).items() if not k.startswith("_")}
    ctx.trust_boundary.validate_config_seal(config_data) # Should pass
    
    # Tamper with the internal config (directly for testing)
    tampered_config = config_data.copy()
    if "fail_fast" in tampered_config:
        tampered_config["fail_fast"] = not tampered_config["fail_fast"]
    else:
        tampered_config["TAMPERED"] = True
    
    with pytest.raises(ArtifactIntegrityError) as excinfo:
        ctx.trust_boundary.validate_config_seal(tampered_config)
    assert "Configuration seal violation" in str(excinfo.value)
