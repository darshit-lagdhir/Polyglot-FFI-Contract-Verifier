import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    AbiNegotiationEngine,
    RuntimePlatformSignature
)

def test_abi_runtime_signature_detection():
    """Verify that ABI signature detection captures all required fields."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp",
        abi_bits=64,
        descriptors={},
        custom_metadata={"endianness": "little"}
    )
    ctx = EnforcementContext("test_fp", meta)
    engine = ctx.abi_engine
    
    sig = engine._runtime_signature
    assert isinstance(sig, RuntimePlatformSignature)
    assert sig.pointer_size_bits in [32, 64]
    assert sig.endianness in ["little", "big"]
    assert sig.architecture != "unknown"
    assert sig.platform_identifier != "unknown"
    assert isinstance(sig.calling_convention_support, list)
    assert len(sig.calling_convention_support) > 0

def test_abi_compatibility_report_generation():
    """Verify deterministic ABI compatibility report generation."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_fp",
        abi_bits=64,
        descriptors={},
        custom_metadata={"endianness": "little"}
    )
    ctx = EnforcementContext("test_fp", meta)
    report = ctx.abi_engine.generate_abi_compatibility_report()
    
    assert "runtime_signature" in report
    assert "contract_abi_metadata" in report
    assert "compatibility_result" in report
    assert "negotiation_status" in report
    assert report["negotiation_status"] in ["ACCEPTED", "REJECTED"]
