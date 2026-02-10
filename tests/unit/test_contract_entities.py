"""
Unit tests for Module 06: Contract Entities
Test suite (85 tests)
"""

import pytest
from pathlib import Path
import sys
import json
from datetime import datetime

# Add modules directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_entities import (
    SchemaVersion, GenerationMode, Severity, ClauseType, SubjectKind,
    GenerationMetadata, ContractHeader, SubjectReference,
    ConstraintParameter, ContractClause, ContractDocument
)

class TestGenerationMetadata:
    """Test GenerationMetadata entity."""
    
    def test_creation_with_defaults(self):
        metadata = GenerationMetadata()
        
        assert metadata.tool_name == "pfcv-contract-gen"
        assert metadata.tool_version == "1.0.0"
        assert metadata.generation_mode == GenerationMode.AUTO
        assert metadata.generation_timestamp != ""
    
    def test_timestamp_auto_generation(self):
        metadata = GenerationMetadata()
        
        # Should be ISO format
        assert 'T' in metadata.generation_timestamp
        assert len(metadata.generation_timestamp) > 10
    
    def test_custom_values(self):
        metadata = GenerationMetadata(
            tool_name="custom-tool",
            tool_version="2.0.0",
            generation_mode=GenerationMode.MANUAL,
            ir_artifact_hash="abc123"
        )
        
        assert metadata.tool_name == "custom-tool"
        assert metadata.tool_version == "2.0.0"
        assert metadata.generation_mode == GenerationMode.MANUAL
        assert metadata.ir_artifact_hash == "abc123"
    
    def test_serialization(self):
        metadata = GenerationMetadata(
            generation_mode=GenerationMode.HYBRID,
            ir_artifact_hash="test_hash"
        )
        
        data = metadata.to_dict()
        
        assert data['tool_name'] == "pfcv-contract-gen"
        assert data['generation_mode'] == "hybrid"
        assert data['ir_artifact_hash'] == "test_hash"
    
    def test_deserialization(self):
        data = {
            'tool_name': 'test-tool',
            'tool_version': '1.5.0',
            'generation_mode': 'manual',
            'ir_artifact_hash': 'hash123'
        }
        
        metadata = GenerationMetadata.from_dict(data)
        
        assert metadata.tool_name == 'test-tool'
        assert metadata.generation_mode == GenerationMode.MANUAL

class TestContractHeader:
    """Test ContractHeader entity."""
    
    def test_creation_with_defaults(self):
        header = ContractHeader(target_interface_id="test_interface")
        
        assert header.schema_version == "1.0.0"
        assert header.contract_version == "1.0.0"
        assert header.target_interface_id == "test_interface"
        assert header.contract_id is not None
    
    def test_contract_id_generation(self):
        header1 = ContractHeader(target_interface_id="interface_1")
        header2 = ContractHeader(target_interface_id="interface_1")
        header3 = ContractHeader(target_interface_id="interface_2")
        
        # Same interface and version should generate same ID
        assert header1.contract_id == header2.contract_id
        
        # Different interface should generate different ID
        assert header1.contract_id != header3.contract_id
    
    def test_validation_success(self):
        header = ContractHeader(target_interface_id="test_id")
        
        errors = header.validate()
        
        assert len(errors) == 0
    
    def test_validation_invalid_schema_version(self):
        header = ContractHeader(
            schema_version="invalid",
            target_interface_id="test_id"
        )
        
        errors = header.validate()
        
        assert len(errors) > 0
        assert any("schema_version" in e for e in errors)
    
    def test_validation_invalid_contract_version(self):
        header = ContractHeader(
            contract_version="not_semver",
            target_interface_id="test_id"
        )
        
        errors = header.validate()
        
        assert len(errors) > 0
        assert any("contract_version" in e for e in errors)
    
    def test_validation_missing_target(self):
        header = ContractHeader(target_interface_id="")
        
        errors = header.validate()
        
        assert len(errors) > 0
        assert any("target_interface_id" in e for e in errors)
    
    def test_semver_validation(self):
        header = ContractHeader(target_interface_id="test")
        
        assert header._is_valid_semver("1.0.0")
        assert header._is_valid_semver("2.3.4")
        assert not header._is_valid_semver("1.0")
        assert not header._is_valid_semver("1.0.0.0")
        assert not header._is_valid_semver("abc")
    
    def test_serialization(self):
        header = ContractHeader(
            contract_name="TestContract",
            target_interface_id="interface_123",
            description="Test contract"
        )
        
        data = header.to_dict()
        
        assert data['contract_name'] == "TestContract"
        assert data['target_interface_id'] == "interface_123"
        assert data['description'] == "Test contract"
    
    def test_deserialization(self):
        data = {
            'schema_version': '1.0.0',
            'contract_version': '2.0.0',
            'contract_name': 'MyContract',
            'target_interface_id': 'interface_abc'
        }
        
        header = ContractHeader.from_dict(data)
        
        assert header.contract_version == '2.0.0'
        assert header.contract_name == 'MyContract'

class TestSubjectReference:
    """Test SubjectReference entity."""
    
    def test_simple_reference(self):
        ref = SubjectReference(
            subject_kind=SubjectKind.FUNCTION,
            entity_id="func_123"
        )
        
        assert ref.subject_kind == SubjectKind.FUNCTION
        assert ref.entity_id == "func_123"
        assert ref.parent_id is None
    
    def test_nested_reference(self):
        ref = SubjectReference(
            subject_kind=SubjectKind.PARAMETER,
            entity_id="param_1",
            parent_id="func_123",
            index=0
        )
        
        assert ref.subject_kind == SubjectKind.PARAMETER
        assert ref.parent_id == "func_123"
        assert ref.index == 0
    
    def test_string_representation(self):
        ref = SubjectReference(
            subject_kind=SubjectKind.FUNCTION,
            entity_id="func_123"
        )
        
        str_repr = str(ref)
        
        assert "function" in str_repr
        assert "func_123" in str_repr
    
    def test_serialization(self):
        ref = SubjectReference(
            subject_kind=SubjectKind.FIELD,
            entity_id="field_x",
            parent_id="struct_Point",
            index=0
        )
        
        data = ref.to_dict()
        
        assert data['subject_kind'] == 'field'
        assert data['entity_id'] == 'field_x'
        assert data['parent_id'] == 'struct_Point'
        assert data['index'] == 0
    
    def test_deserialization(self):
        data = {
            'subject_kind': 'parameter',
            'entity_id': 'param_data',
            'parent_id': 'func_process'
        }
        
        ref = SubjectReference.from_dict(data)
        
        assert ref.subject_kind == SubjectKind.PARAMETER
        assert ref.entity_id == 'param_data'

class TestConstraintParameter:
    """Test ConstraintParameter entity."""
    
    def test_integer_parameter(self):
        param = ConstraintParameter(
            name="min_size",
            value=10,
            value_type="integer"
        )
        
        assert param.name == "min_size"
        assert param.value == 10
        assert param.value_type == "integer"
    
    def test_boolean_parameter(self):
        param = ConstraintParameter(
            name="nullable",
            value=True,
            value_type="boolean"
        )
        
        assert param.value is True
        assert param.value_type == "boolean"
    
    def test_string_parameter(self):
        param = ConstraintParameter(
            name="constraint_name",
            value="must_be_aligned",
            value_type="string"
        )
        
        assert param.value == "must_be_aligned"
    
    def test_validation_success(self):
        param = ConstraintParameter(
            name="test",
            value=42,
            value_type="integer"
        )
        
        errors = param.validate()
        
        assert len(errors) == 0
    
    def test_validation_invalid_type(self):
        param = ConstraintParameter(
            name="test",
            value=42,
            value_type="invalid_type"
        )
        
        errors = param.validate()
        
        assert len(errors) > 0
    
    def test_serialization(self):
        param = ConstraintParameter(
            name="alignment",
            value=8,
            value_type="integer"
        )
        
        data = param.to_dict()
        
        assert data['name'] == "alignment"
        assert data['value'] == 8
        assert data['value_type'] == "integer"

class TestContractClause:
    """Test ContractClause entity."""
    
    def test_creation(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func_123")
        
        clause = ContractClause(
            clause_id="clause_001",
            clause_type=ClauseType.NULLABILITY,
            subject_reference=ref
        )
        
        assert clause.clause_id == "clause_001"
        assert clause.clause_type == ClauseType.NULLABILITY
        assert clause.severity == Severity.ERROR
    
    def test_with_parameters(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "param_ptr")
        param = ConstraintParameter("nullable", False, "boolean")
        
        clause = ContractClause(
            clause_id="clause_002",
            clause_type=ClauseType.NULLABILITY,
            subject_reference=ref,
            constraint_parameters=[param]
        )
        
        assert len(clause.constraint_parameters) == 1
        assert clause.get_parameter("nullable").value is False
    
    def test_get_parameter(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        param1 = ConstraintParameter("size", 10, "integer")
        param2 = ConstraintParameter("align", 8, "integer")
        
        clause = ContractClause(
            clause_id="clause_003",
            clause_type=ClauseType.SIZE,
            subject_reference=ref,
            constraint_parameters=[param1, param2]
        )
        
        found = clause.get_parameter("align")
        assert found is not None
        assert found.value == 8
        
        not_found = clause.get_parameter("nonexistent")
        assert not_found is None
    
    def test_validation_success(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        param = ConstraintParameter("test", 1, "integer")
        
        clause = ContractClause(
            clause_id="valid_clause",
            clause_type=ClauseType.SIZE,
            subject_reference=ref,
            constraint_parameters=[param]
        )
        
        errors = clause.validate_structure()
        
        assert len(errors) == 0
    
    def test_validation_missing_clause_id(self):
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        
        clause = ContractClause(
            clause_id="",
            clause_type=ClauseType.SIZE,
            subject_reference=ref
        )
        
        errors = clause.validate_structure()
        
        assert len(errors) > 0
        assert any("clause_id" in e for e in errors)
    
    def test_serialization(self):
        ref = SubjectReference(SubjectKind.PARAMETER, "param")
        param = ConstraintParameter("nullable", False, "boolean")
        
        clause = ContractClause(
            clause_id="clause_test",
            clause_type=ClauseType.NULLABILITY,
            subject_reference=ref,
            constraint_parameters=[param],
            explanation="Must not be null"
        )
        
        data = clause.to_dict()
        
        assert data['clause_id'] == "clause_test"
        assert data['clause_type'] == "nullability"
        assert data['explanation'] == "Must not be null"

class TestContractDocument:
    """Test ContractDocument entity."""
    
    def test_creation(self):
        header = ContractHeader(target_interface_id="test_interface")
        doc = ContractDocument(header=header)
        
        assert doc.header.target_interface_id == "test_interface"
        assert len(doc.clauses) == 0
    
    def test_add_clause(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause(
            clause_id="clause_1",
            clause_type=ClauseType.SIZE,
            subject_reference=ref
        )
        
        doc.add_clause(clause)
        
        assert len(doc.clauses) == 1
    
    def test_get_clause(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause(
            clause_id="findme",
            clause_type=ClauseType.SIZE,
            subject_reference=ref
        )
        
        doc.add_clause(clause)
        
        found = doc.get_clause("findme")
        assert found is not None
        assert found.clause_id == "findme"
        
        not_found = doc.get_clause("nonexistent")
        assert not_found is None
    
    def test_get_clauses_by_type(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        
        clause1 = ContractClause("c1", ClauseType.SIZE, ref)
        clause2 = ContractClause("c2", ClauseType.NULLABILITY, ref)
        clause3 = ContractClause("c3", ClauseType.SIZE, ref)
        
        doc.add_clause(clause1)
        doc.add_clause(clause2)
        doc.add_clause(clause3)
        
        size_clauses = doc.get_clauses_by_type(ClauseType.SIZE)
        
        assert len(size_clauses) == 2
    
    def test_validation_success(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("c1", ClauseType.SIZE, ref)
        doc.add_clause(clause)
        
        errors = doc.validate_structure()
        
        assert len(errors) == 0
    
    def test_validation_duplicate_clause_ids(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause1 = ContractClause("duplicate", ClauseType.SIZE, ref)
        clause2 = ContractClause("duplicate", ClauseType.NULLABILITY, ref)
        
        doc.add_clause(clause1)
        doc.add_clause(clause2)
        
        errors = doc.validate_structure()
        
        assert len(errors) > 0
        assert any("Duplicate" in e for e in errors)
    
    def test_serialization(self):
        header = ContractHeader(
            contract_name="TestContract",
            target_interface_id="test_id"
        )
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("c1", ClauseType.SIZE, ref)
        doc.add_clause(clause)
        
        data = doc.to_dict()
        
        assert 'header' in data
        assert 'clauses' in data
        assert len(data['clauses']) == 1
    
    def test_json_serialization(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        json_str = doc.to_json()
        
        assert isinstance(json_str, str)
        assert "header" in json_str
        assert "clauses" in json_str
    
    def test_json_deserialization(self):
        header = ContractHeader(target_interface_id="test")
        doc = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("c1", ClauseType.SIZE, ref)
        doc.add_clause(clause)
        
        json_str = doc.to_json()
        restored = ContractDocument.from_json(json_str)
        
        assert restored.header.target_interface_id == "test"
        assert len(restored.clauses) == 1

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
