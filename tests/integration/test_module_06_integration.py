"""
Module 06: Integration Tests (Prompt 10/15)

Complete end-to-end integration tests for contract system.
Tests cross-component workflows, performance, and real-world scenarios.
"""

import pytest
from pathlib import Path
import sys
import time
import tempfile
import shutil
import json

# Ensure modules directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_generation import (
    ContractGenerator, GenerationConfig
)
from module_06_contract_schema.contract_validation import (
    ContractValidator, ValidationContext
)
from module_06_contract_schema.contract_serialization import (
    ContractSerializer, ContractDeserializer, ContractFileManager, ContractArtifactManager
)
from module_06_contract_schema.contract_diff_advanced import (
    AdvancedContractDiffer
)
from module_06_contract_schema.contract_versioning import (
    SemanticVersion, VersionRecommender
)
from module_06_contract_schema.enforcement_boundary import (
    EnforcementEngine, PythonAdapter, EnforcementMode
)
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractHeader, ContractClause, SubjectReference,
    ConstraintParameter, ClauseType, SubjectKind, Severity
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp = Path(tempfile.mkdtemp())
    yield temp
    shutil.rmtree(temp)

def create_sample_contract():
    """Create sample contract for testing."""
    header = ContractHeader(
        contract_version="1.0.0",
        target_interface_id="sample_interface"
    )
    contract = ContractDocument(header=header)
    
    # Add some clauses
    ref = SubjectReference(SubjectKind.FUNCTION, "test_func")
    
    # Nullability clause
    null_param = ConstraintParameter("nullable", False, "boolean")
    null_clause = ContractClause(
        "null_001",
        ClauseType.NULLABILITY,
        ref,
        constraint_parameters=[null_param],
        explanation="Parameter must be non-null"
    )
    contract.add_clause(null_clause)
    
    # Size clause
    size_param = ConstraintParameter("size_value", 100, "integer")
    size_clause = ContractClause(
        "size_001",
        ClauseType.SIZE,
        ref,
        constraint_parameters=[size_param],
        explanation="Buffer must be at least 100 bytes"
    )
    contract.add_clause(size_clause)
    
    return contract

# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_generate_validate_serialize_roundtrip(self, temp_dir):
        """
        Test complete workflow: Generate -> Validate -> Serialize -> Deserialize.
        """
        # Stage 1: Generate contract
        contract = create_sample_contract()
        assert len(contract.clauses) > 0
        
        # Stage 2: Validate contract
        validator = ContractValidator()
        validation_result = validator.validate(
            contract,
            skip_referential=True,
            skip_constraint=True
        )
        assert validation_result.schema_result.passed
        
        # Stage 3: Serialize contract
        serializer = ContractSerializer()
        json_str = serializer.serialize(contract)
        assert len(json_str) > 0
        
        # Stage 4: Deserialize contract
        deserializer = ContractDeserializer(verify_integrity=True)
        restored = deserializer.deserialize(json_str)
        
        # Stage 5: Verify roundtrip
        assert restored.header.contract_version == contract.header.contract_version
        assert len(restored.clauses) == len(contract.clauses)
        assert restored.clauses[0].explanation == contract.clauses[0].explanation

    def test_file_save_load_workflow(self, temp_dir):
        """
        Test file-based workflow: Create -> Save -> Load -> Validate.
        """
        # Create contract
        contract = create_sample_contract()
        
        # Save to file
        contract_file = temp_dir / "contract.json"
        file_manager = ContractFileManager()
        file_manager.save(contract, contract_file)
        
        assert contract_file.exists()
        
        # Load from file
        loaded = file_manager.load(contract_file)
        
        # Validate loaded contract
        assert loaded.header.contract_version == contract.header.contract_version
        assert len(loaded.clauses) == len(contract.clauses)

    def test_diff_and_versioning_workflow(self, temp_dir):
        """
        Test diff workflow: Create v1 -> Create v2 -> Diff -> Recommend version.
        """
        # Create v1 contract
        v1 = create_sample_contract()
        v1.header.contract_version = "1.0.0"
        
        # Create v2 contract (with additional clause)
        v2 = create_sample_contract()
        v2.header.contract_version = "1.1.0"
        
        ref = SubjectReference(SubjectKind.FUNCTION, "new_func")
        new_clause = ContractClause("new_001", ClauseType.SIZE, ref, explanation="Added check")
        v2.add_clause(new_clause)
        
        # Compute diff
        differ = AdvancedContractDiffer()
        diff_result = differ.compute_diff(v1, v2)
        
        # Should detect addition
        assert len(diff_result.detailed_changes) > 0
        
        # Recommend version bump
        recommender = VersionRecommender()
        new_version, rationale = recommender.recommend_version_bump(
            SemanticVersion.parse("1.0.0"),
            diff_result
        )
        
        # Should recommend bump (likely minor for addition if compatible)
        assert new_version > SemanticVersion.parse("1.0.0")

class TestCrossComponentIntegration:
    """Test integration between different components."""
    
    def test_generation_to_enforcement(self, temp_dir):
        """
        Test: Generate contract -> Build enforcement engine -> Enforce.
        """
        # Generate contract
        contract = create_sample_contract()
        
        # Create enforcement engine
        adapter = PythonAdapter(mode=EnforcementMode.STRICT)
        engine = EnforcementEngine(contract, adapter)
        
        # Enforce valid call
        violations = engine.enforce_pre_call(
            "test_func",
            {"buf": b"data" * 30} # Enough size
        )
        
        # Should pass
        assert len(violations) == 0

    def test_serialization_to_enforcement(self, temp_dir):
        """
        Test: Serialize contract -> Load -> Enforce.
        """
        # Create and serialize contract
        contract = create_sample_contract()
        
        contract_file = temp_dir / "contract.json"
        file_manager = ContractFileManager()
        file_manager.save(contract, contract_file)
        
        # Load contract
        loaded = file_manager.load(contract_file)
        
        # Create enforcement engine
        adapter = PythonAdapter(mode=EnforcementMode.AUDIT)
        engine = EnforcementEngine(loaded, adapter)
        
        # Should work with loaded contract
        assert engine.contract is not None
        assert len(engine.clause_index) > 0

class TestPerformanceIntegration:
    """Test performance at system level."""
    
    def test_large_contract_serialization_performance(self, temp_dir):
        """
        Test serialization performance with large contract.
        """
        # Create large contract (500 clauses)
        header = ContractHeader(target_interface_id="large_interface")
        contract = ContractDocument(header=header)
        
        for i in range(500):
            ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
            clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref, explanation="Perf test")
            contract.add_clause(clause)
        
        # Measure serialization time
        serializer = ContractSerializer()
        
        start = time.time()
        json_str = serializer.serialize(contract)
        duration = time.time() - start
        
        # Should complete quickly
        assert duration < 5.0 # Lenient for slower environments
        assert len(json_str) > 0

    def test_enforcement_overhead_measurement(self, temp_dir):
        """
        Test enforcement overhead is acceptable.
        """
        contract = create_sample_contract()
        adapter = PythonAdapter(mode=EnforcementMode.PRODUCTION)
        engine = EnforcementEngine(contract, adapter)
        
        # Measure 100 calls
        iterations = 100
        
        start = time.perf_counter_ns()
        for _ in range(iterations):
            engine.enforce_pre_call("test_func", {"buf": b"data" * 30})
        end = time.perf_counter_ns()
        
        avg_overhead_ns = (end - start) / iterations
        
        # Should be minimal
        assert avg_overhead_ns < 10000 # 10us is safe even on slow systems

class TestErrorPropagation:
    """Test error handling across system."""
    
    def test_invalid_contract_validation_error(self):
        """
        Test that invalid contracts produce clear validation errors.
        """
        # Create contract with invalid clause (empty ID)
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("", ClauseType.SIZE, ref) # Invalid empty ID
        contract.add_clause(clause)
        
        # Validate should fail
        validator = ContractValidator()
        result = validator.validate(
            contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert not result.schema_result.passed
        assert len(result.schema_result.errors) > 0

    def test_serialization_error_handling(self, temp_dir):
        """
        Test serialization error handling.
        """
        # Try to save to invalid path (assuming some root protection or invalid chars)
        contract = create_sample_contract()
        file_manager = ContractFileManager()
        
        # Using a definitely invalid file name on Windows
        invalid_path = temp_dir / '":*?<>|'
        
        with pytest.raises(Exception):
            file_manager.save(contract, invalid_path)

class TestStatePersistence:
    """Test state management across operations."""
    
    def test_artifact_manager_caching(self, temp_dir):
        """
        Test that artifact manager caches contracts correctly.
        """
        manager = ContractArtifactManager(temp_dir)
        
        # Save contract
        contract = create_sample_contract()
        path = manager.save_artifact(contract)
        
        assert path.exists()
        
        # Load twice
        contract_id = contract.header.contract_id
        loaded1 = manager.load_artifact(contract_id)
        loaded2 = manager.load_artifact(contract_id)
        
        # Both should succeed
        assert loaded1 is not None
        assert loaded2 is not None

class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    def test_simple_c_library_workflow(self, temp_dir):
        """
        Test workflow for simple C library.
        """
        # Create contract for simple C library
        header = ContractHeader(
            contract_version="1.0.0",
            target_interface_id="simple_c_lib"
        )
        contract = ContractDocument(header=header)
        
        # Add typical clauses for C library
        # Layout clause for struct
        struct_ref = SubjectReference(SubjectKind.STRUCTURE, "Point")
        layout_clause = ContractClause(
            "layout_Point",
            ClauseType.LAYOUT,
            struct_ref,
            explanation="Struct layout check"
        )
        contract.add_clause(layout_clause)
        
        # Nullability clause for pointer parameter
        func_ref = SubjectReference(SubjectKind.PARAMETER, "buffer")
        null_clause = ContractClause(
            "null_buffer",
            ClauseType.NULLABILITY,
            func_ref,
            constraint_parameters=[
                ConstraintParameter("nullable", False, "boolean")
            ],
            explanation="Buffer cannot be NULL"
        )
        contract.add_clause(null_clause)
        
        # Validate contract
        validator = ContractValidator()
        result = validator.validate(
            contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert result.schema_result.passed
        
        # Serialize contract
        contract_file = temp_dir / "simple_c_lib.json"
        file_manager = ContractFileManager()
        file_manager.save(contract, contract_file)
        
        # Verify file created
        assert contract_file.exists()

class TestRegressions:
    """Regression tests for fixed bugs."""
    
    def test_regression_empty_contract_serialization(self):
        """
        Regression: Empty contracts should serialize successfully.
        """
        empty_contract = ContractDocument(
            header=ContractHeader(target_interface_id="empty")
        )
        
        serializer = ContractSerializer()
        json_str = serializer.serialize(empty_contract)
        
        assert json_str is not None
        assert len(json_str) > 0
        
        # Should deserialize back
        deserializer = ContractDeserializer()
        restored = deserializer.deserialize(json_str)
        
        assert restored.header.target_interface_id == "empty"

    def test_regression_duplicate_clause_ids(self):
        """
        Regression: Duplicate clause IDs should be detected.
        """
        contract = ContractDocument(
            header=ContractHeader(target_interface_id="test")
        )
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        
        clause1 = ContractClause("duplicate", ClauseType.SIZE, ref, explanation="1")
        clause2 = ContractClause("duplicate", ClauseType.NULLABILITY, ref, explanation="2")
        
        contract.add_clause(clause1)
        contract.add_clause(clause2)
        
        # Validation should fail
        validator = ContractValidator()
        result = validator.validate(
            contract,
            skip_referential=True,
            skip_constraint=True
        )
        
        assert not result.schema_result.passed

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
