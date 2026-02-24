import pytest
import hashlib
import json
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    InvocationOrchestrator,
    ValidationGraph,
    ValidationEngine,
    OwnershipRichRegistry,
    InvocationState,
    RecoveryReport
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_deterministic_recovery_report():
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise ValueError("Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    reports = []
    
    # Run recovery twice with same inputs
    for i in range(2):
        # Reset state for fresh test within same context if needed, but here we want to see if report is stable
        try:
             # Force deterministic sequence index
             ctx.invocation_sequence_counter = 100
             orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
        except ValueError as e:
            # Manually trigger recovery for inspection since raise usually exits
            # But execute_pipeline ALREADY calls it. 
            # We can capture it by mocking the perform_recovery method
            pass
            
    # Let's test perform_recovery directly
    err = ValueError("Failure")
    r1 = ctx.recovery_orchestrator.perform_recovery(InvocationState.INVOCATION_VALIDATING, err)
    r2 = ctx.recovery_orchestrator.perform_recovery(InvocationState.INVOCATION_VALIDATING, err)
    
    # Reports should be deterministic if sequence and actions are same
    # Note: recovery_count increments, so we might need to adjust
    assert r1.failure_stage == r2.failure_stage
    assert r1.rollback_actions_performed == r2.rollback_actions_performed
    assert r1.failure_classification == r2.failure_classification
