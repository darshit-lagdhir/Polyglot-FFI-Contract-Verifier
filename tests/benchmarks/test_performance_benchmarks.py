""" 
Module 06: Performance Benchmarks

Comprehensive performance benchmarking suite for Module 06. 
Uses pytest-benchmark for accurate measurements. 
"""

import pytest
from pathlib import Path
import sys
import os

# Add modules to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'modules'))

from module_06_contract_schema import (
    ContractGenerator,
    ContractValidator,
    ContractSerializer,
    ContractDeserializer,
    AdvancedContractDiffer,
    EnforcementEngine,
    PythonAdapter,
    ContractDocument,
    ContractHeader,
    ContractClause,
    SubjectReference,
    SubjectKind,
    ClauseType,
    ConstraintParameter
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def small_contract():
    """Create small contract (50 clauses)."""
    header = ContractHeader(target_interface_id="small")
    contract = ContractDocument(header=header)
    
    for i in range(50):
        ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
        clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
    return contract

@pytest.fixture
def medium_contract():
    """Create medium contract (500 clauses)."""
    header = ContractHeader(target_interface_id="medium")
    contract = ContractDocument(header=header)
    
    for i in range(500):
        ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
        clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
    return contract

@pytest.fixture
def large_contract():
    """Create large contract (2000 clauses)."""
    header = ContractHeader(target_interface_id="large")
    contract = ContractDocument(header=header)
    
    for i in range(2000):
        ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
        clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
    return contract

# ============================================================================
# GENERATION BENCHMARKS
# ============================================================================

class TestGenerationBenchmarks:
    """Benchmark contract generation."""
    
    def test_generation_small(self, benchmark):
        """Benchmark generation with small mock IR."""
        generator = ContractGenerator()
        
        result = benchmark(
            generator.generate,
            None,  # Mock IR handled inside generate prototype
            "benchmark_small"
        )
        
        assert result is not None

# ============================================================================
# VALIDATION BENCHMARKS
# ============================================================================

class TestValidationBenchmarks:
    """Benchmark contract validation."""
    
    def test_validation_schema_small(self, benchmark, small_contract):
        """Benchmark schema validation (small contract)."""
        validator = ContractValidator()
        
        result = benchmark(
            validator.validate,
            small_contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert result.schema_result is not None

    def test_validation_schema_medium(self, benchmark, medium_contract):
        """Benchmark schema validation (medium contract)."""
        validator = ContractValidator()
        
        result = benchmark(
            validator.validate,
            medium_contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert result.schema_result is not None

    def test_validation_schema_large(self, benchmark, large_contract):
        """Benchmark schema validation (large contract)."""
        validator = ContractValidator()
        
        result = benchmark(
            validator.validate,
            large_contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert result.schema_result is not None

# ============================================================================
# SERIALIZATION BENCHMARKS
# ============================================================================

class TestSerializationBenchmarks:
    """Benchmark contract serialization."""
    
    def test_serialize_small(self, benchmark, small_contract):
        """Benchmark serialization (small contract)."""
        serializer = ContractSerializer()
        
        result = benchmark(serializer.serialize, small_contract)
        
        assert len(result) > 0

    def test_serialize_medium(self, benchmark, medium_contract):
        """Benchmark serialization (medium contract)."""
        serializer = ContractSerializer()
        
        result = benchmark(serializer.serialize, medium_contract)
        
        assert len(result) > 0

    def test_deserialize_medium(self, benchmark, medium_contract):
        """Benchmark deserialization (medium contract)."""
        serializer = ContractSerializer()
        json_str = serializer.serialize(medium_contract)
        
        deserializer = ContractDeserializer(verify_integrity=False)
        
        result = benchmark(deserializer.deserialize, json_str)
        
        assert result is not None

# ============================================================================
# DIFFING BENCHMARKS
# ============================================================================

class TestDiffingBenchmarks:
    """Benchmark contract diffing."""
    
    def test_diff_medium_contracts(self, benchmark, medium_contract):
        """Benchmark diffing medium contracts."""
        # Create slightly modified version
        v2 = ContractDocument(
            header=ContractHeader(
                target_interface_id="medium",
                contract_version="2.0.0"
            )
        )
        
        for i in range(500):
            ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
            # Slightly different logic: every 10th is NULLABILITY instead of SIZE
            ctype = ClauseType.NULLABILITY if i % 10 == 0 else ClauseType.SIZE
            clause = ContractClause(f"clause_{i}", ctype, ref)
            v2.add_clause(clause)
        
        # Add one new clause
        ref = SubjectReference(SubjectKind.FUNCTION, "func_new")
        new_clause = ContractClause("clause_new", ClauseType.SIZE, ref)
        v2.add_clause(new_clause)
        
        differ = AdvancedContractDiffer()
        
        # Use diff from AdvancedContractDiffer (which might map to compute_diff)
        # Checking actual method name in AdvancedContractDiffer
        result = benchmark(differ.compute_diff, medium_contract, v2)
        
        assert result is not None

# ============================================================================
# ENFORCEMENT BENCHMARKS
# ============================================================================

class TestEnforcementBenchmarks:
    """Benchmark runtime enforcement."""
    
    def test_enforcement_setup(self, benchmark, small_contract):
        """Benchmark enforcement engine setup."""
        adapter = PythonAdapter()
        
        result = benchmark(EnforcementEngine, small_contract, adapter)
        
        assert result is not None

    def test_enforcement_pre_call(self, benchmark, small_contract):
        """Benchmark pre-call enforcement."""
        adapter = PythonAdapter()
        engine = EnforcementEngine(small_contract, adapter)
        
        # Mock arguments
        args = {"buffer": b"test_data", "ptr": 1234}
        
        # Benchmarking a specific entity enforcement
        result = benchmark(engine.enforce_pre_call, "func_0", args)
        
        assert isinstance(result, list)

    def test_enforcement_post_call(self, benchmark, small_contract):
        """Benchmark post-call enforcement."""
        adapter = PythonAdapter()
        engine = EnforcementEngine(small_contract, adapter)
        
        # Mock result
        ret_val = 0
        
        # Benchmarking a specific entity enforcement
        result = benchmark(engine.enforce_post_call, "func_0", ret_val)
        
        assert isinstance(result, list)

# ============================================================================
# LOOKUP BENCHMARKS
# ============================================================================

class TestLookupBenchmarks:
    """Benchmark lookup operations."""
    
    def test_clause_lookup_by_id(self, benchmark, medium_contract):
        """Benchmark clause lookup by ID."""
        target_id = "clause_250"
        
        result = benchmark(medium_contract.get_clause, target_id)
        
        assert result is not None

    def test_clause_lookup_by_type(self, benchmark, medium_contract):
        """Benchmark clause lookup by type."""
        result = benchmark(
            medium_contract.get_clauses_by_type,
            ClauseType.SIZE
        )
        
        assert len(result) > 0
