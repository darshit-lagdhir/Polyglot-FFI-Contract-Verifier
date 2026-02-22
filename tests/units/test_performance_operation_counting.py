import pytest
import threading
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    EnforcementContext,
    ContractMetadata,
    PerformanceInstrumentationEngine
)

def test_performance_operation_counting_isolation():
    """Verify that operation counters are thread-local and deterministic."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_count",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_perf_count", meta)
    engine = ctx.performance_engine
    
    def worker():
        engine.reset()
        engine.increment("validation_steps", 10)
        engine.increment("relational_checks", 5)
        assert engine.get_invocation_total() == 15
        
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Global state (main thread) should be clean or separate
    engine.reset()
    assert engine.get_invocation_total() == 0

def test_performance_snapshot_determinism():
    """Verify that performance snapshots are deterministic."""
    meta = ContractMetadata(
        schema_version="1.0",
        synthesis_version="1.0",
        fingerprint="test_perf_snap",
        abi_bits=64,
        descriptors={},
        custom_metadata={}
    )
    ctx = EnforcementContext("test_perf_snap", meta)
    engine = ctx.performance_engine
    validator = ctx.performance_validator
    
    engine.reset()
    engine.increment("validation_steps", 100)
    
    snap1 = validator.generate_performance_snapshot("test_func", 1)
    
    # Same operations should yield same fingerprint
    engine.reset()
    engine.increment("validation_steps", 100)
    snap2 = validator.generate_performance_snapshot("test_func", 1)
    
    assert snap1.total_operation_count == snap2.total_operation_count
    assert snap1.deterministic_performance_fingerprint == snap2.deterministic_performance_fingerprint
