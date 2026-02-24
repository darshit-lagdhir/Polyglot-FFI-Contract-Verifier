import pytest
import hashlib
import json
import threading
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    InvocationOrchestrator,
    ValidationGraph,
    ValidationEngine,
    OwnershipRichRegistry,
    HierarchicalLock
)

def _meta():
    m = ContractMetadata(schema_version="1.0", synthesis_version="1.0", fingerprint="", abi_bits=64, descriptors={})
    m_dict = asdict(m)
    fp = hashlib.sha256(json.dumps(m_dict, sort_keys=True).encode()).hexdigest()[:32]
    return m, fp

def test_recovery_deadlock_free_under_concurrent_failure():
    """Verify that recovery doesn't deadlock when multiple invocations fail concurrently."""
    meta, fp = _meta()
    ctx = EnforcementContext(fp, meta)
    
    class FailingEngine(ValidationEngine):
        def validate(self, *args, **kwargs):
            raise RuntimeError("Concur Failure")

    orchestrator = InvocationOrchestrator(FailingEngine(), OwnershipRichRegistry())
    orchestrator.config.enable_pre_validation = True
    
    def run_failing_call():
        try:
            orchestrator.execute_pipeline("f", ValidationGraph(function_name="f"), [], ctx)
        except RuntimeError:
            pass
            
    threads = [threading.Thread(target=run_failing_call) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=2.0)
    
    for t in threads:
        assert not t.is_alive(), "Thread deadlocked during recovery"
    
    assert ctx.recovery_orchestrator.recovery_count == 5
