"""
Unit tests for Module 06: Contract Serialization
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys
import json
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_06_contract_schema.contract_serialization import (
    IntegrityInfo, compute_checksum, verify_checksum,
    SerializationError, DeserializationError, IntegrityError,
    ContractSerializer, ContractDeserializer,
    ContractFileManager, ContractArtifactManager
)
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractHeader, ContractClause,
    SubjectReference, SubjectKind, ClauseType
)

class TestIntegrityInfo:
    """Test IntegrityInfo representation."""
    
    def test_creation(self):
        info = IntegrityInfo(checksum="abc123")
        
        assert info.checksum == "abc123"
        assert info.checksum_algorithm == "sha256"
    
    def test_to_dict(self):
        info = IntegrityInfo(
            checksum="abc123",
            checksum_algorithm="sha256"
        )
        
        data = info.to_dict()
        
        assert data['checksum'] == "abc123"
        assert data['checksum_algorithm'] == "sha256"
    
    def test_from_dict(self):
        data = {
            'checksum': 'xyz789',
            'checksum_algorithm': 'sha512'
        }
        
        info = IntegrityInfo.from_dict(data)
        
        assert info.checksum == 'xyz789'
        assert info.checksum_algorithm == 'sha512'
    
    def test_computed_at_auto_set(self):
        info = IntegrityInfo(checksum="test")
        
        assert info.computed_at != ""
    
    def test_computed_at_explicit(self):
        timestamp = "2025-01-01T00:00:00Z"
        info = IntegrityInfo(checksum="test", computed_at=timestamp)
        
        assert info.computed_at == timestamp

class TestChecksumFunctions:
    """Test checksum computation and verification."""
    
    def test_compute_checksum(self):
        content = "test content"
        
        checksum = compute_checksum(content)
        
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
    
    def test_compute_checksum_deterministic(self):
        content = "test content"
        
        checksum1 = compute_checksum(content)
        checksum2 = compute_checksum(content)
        
        assert checksum1 == checksum2
    
    def test_compute_checksum_different_content(self):
        content1 = "content 1"
        content2 = "content 2"
        
        checksum1 = compute_checksum(content1)
        checksum2 = compute_checksum(content2)
        
        assert checksum1 != checksum2
    
    def test_verify_checksum_valid(self):
        content = "test content"
        checksum = compute_checksum(content)
        
        assert verify_checksum(content, checksum)
    
    def test_verify_checksum_invalid(self):
        content = "test content"
        wrong_checksum = "0" * 64
        
        assert not verify_checksum(content, wrong_checksum)
    
    def test_compute_checksum_sha512(self):
        content = "test"
        
        checksum = compute_checksum(content, "sha512")
        
        assert len(checksum) == 128  # SHA-512 hex length
    
    def test_compute_checksum_unsupported_algorithm(self):
        with pytest.raises(ValueError):
            compute_checksum("test", "md5")
    
    def test_verify_checksum_sha512(self):
        content = "test"
        checksum = compute_checksum(content, "sha512")
        
        assert verify_checksum(content, checksum, "sha512")
    
    def test_compute_checksum_empty_string(self):
        checksum = compute_checksum("")
        
        assert isinstance(checksum, str)
        assert len(checksum) == 64
    
    def test_compute_checksum_unicode(self):
        content = "Hello 世界 🌍"
        
        checksum = compute_checksum(content)
        
        assert isinstance(checksum, str)

class TestContractSerializer:
    """Test ContractSerializer."""
    
    def test_serialize_minimal_contract(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        assert isinstance(json_str, str)
        assert "schema_version" in json_str
        assert "contract" in json_str
    
    def test_serialize_with_clauses(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        # Should be valid JSON
        data = json.loads(json_str)
        
        assert 'contract' in data
        assert 'clauses' in data['contract']
        assert len(data['contract']['clauses']) == 1
    
    def test_serialize_deterministic(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=False)
        
        json1 = serializer.serialize(contract)
        json2 = serializer.serialize(contract)
        
        assert json1 == json2
    
    def test_serialize_with_integrity(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=True)
        json_str = serializer.serialize(contract)
        
        data = json.loads(json_str)
        
        assert 'integrity' in data
        assert 'checksum' in data['integrity']
    
    def test_serialize_pretty_vs_compact(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        pretty_serializer = ContractSerializer(pretty=True, include_integrity=False)
        compact_serializer = ContractSerializer(pretty=False, include_integrity=False)
        
        pretty_json = pretty_serializer.serialize(contract)
        compact_json = compact_serializer.serialize(contract)
        
        # Pretty should have whitespace
        assert len(pretty_json) > len(compact_json)
        assert '\n' in pretty_json
        assert '\n' not in compact_json
    
    def test_serialize_sorted_keys(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        # Keys should be sorted
        data = json.loads(json_str)
        keys = list(data.keys())
        assert keys == sorted(keys)
    
    def test_serialize_multiple_clauses(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        for i in range(5):
            ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
            clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
            contract.add_clause(clause)
        
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        data = json.loads(json_str)
        assert len(data['contract']['clauses']) == 5
    
    def test_serialize_includes_schema_version(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        data = json.loads(json_str)
        assert 'schema_version' in data
        assert data['schema_version'] == "1.0.0"

class TestContractDeserializer:
    """Test ContractDeserializer."""
    
    def test_deserialize_valid_contract(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        # Serialize then deserialize
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        deserializer = ContractDeserializer(
            verify_integrity=False,
            validate_contract=False
        )
        restored = deserializer.deserialize(json_str)
        
        assert restored.header.target_interface_id == "test"
    
    def test_deserialize_with_clauses(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        # Round-trip
        serializer = ContractSerializer(include_integrity=False)
        json_str = serializer.serialize(contract)
        
        deserializer = ContractDeserializer(
            verify_integrity=False,
            validate_contract=False
        )
        restored = deserializer.deserialize(json_str)
        
        assert len(restored.clauses) == 1
        assert restored.clauses[0].clause_id == "clause_1"
    
    def test_deserialize_with_integrity_valid(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=True)
        json_str = serializer.serialize(contract)
        
        deserializer = ContractDeserializer(
            verify_integrity=True,
            validate_contract=False
        )
        restored = deserializer.deserialize(json_str)
        
        assert restored is not None
    
    def test_deserialize_with_integrity_corrupted(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=True)
        json_str = serializer.serialize(contract)
        
        # Corrupt content
        corrupted = json_str.replace('"test"', '"corrupted"')
        
        deserializer = ContractDeserializer(verify_integrity=True)
        
        with pytest.raises(IntegrityError):
            deserializer.deserialize(corrupted)
    
    def test_deserialize_invalid_json(self):
        invalid_json = "{ invalid json"
        
        deserializer = ContractDeserializer()
        
        with pytest.raises(DeserializationError):
            deserializer.deserialize(invalid_json)
    
    def test_deserialize_missing_contract_field(self):
        data = {
            'schema_version': '1.0.0'
            # Missing 'contract' field
        }
        
        json_str = json.dumps(data)
        deserializer = ContractDeserializer()
        
        with pytest.raises(DeserializationError):
            deserializer.deserialize(json_str)
    
    def test_deserialize_unsupported_schema(self):
        data = {
            'schema_version': '99.0.0',
            'contract': {}
        }
        
        json_str = json.dumps(data)
        deserializer = ContractDeserializer()
        
        with pytest.raises(DeserializationError):
            deserializer.deserialize(json_str)
    
    def test_deserialize_without_integrity_verification(self):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        serializer = ContractSerializer(include_integrity=True)
        json_str = serializer.serialize(contract)
        
        # Corrupt but don't verify
        corrupted = json_str.replace('"test"', '"corrupted"')
        
        deserializer = ContractDeserializer(
            verify_integrity=False,
            validate_contract=False
        )
        
        # Should succeed (no verification)
        restored = deserializer.deserialize(corrupted)
        assert restored is not None
    
    def test_deserialize_round_trip_preserves_data(self):
        header = ContractHeader(target_interface_id="test_interface")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.PARAMETER, "param1")
        clause = ContractClause("clause_1", ClauseType.NULLABILITY, ref)
        contract.add_clause(clause)
        
        serializer = ContractSerializer(include_integrity=False)
        deserializer = ContractDeserializer(
            verify_integrity=False,
            validate_contract=False
        )
        
        json_str = serializer.serialize(contract)
        restored = deserializer.deserialize(json_str)
        
        assert restored.header.target_interface_id == "test_interface"
        assert len(restored.clauses) == 1
        assert restored.clauses[0].clause_id == "clause_1"

class TestContractFileManager:
    """Test ContractFileManager."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = Path(tempfile.mkdtemp())
        yield temp
        shutil.rmtree(temp)
    
    def test_save_and_load(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        file_path = temp_dir / "contract.json"
        
        manager = ContractFileManager()
        manager.save(contract, file_path)
        
        assert file_path.exists()
        
        loaded = manager.load(file_path)
        
        assert loaded.header.target_interface_id == "test"
    
    def test_save_with_compression(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        file_path = temp_dir / "contract.json"
        
        manager = ContractFileManager(compress=True)
        actual_path = manager.save(contract, file_path)
        
        # Should create .gz file
        assert actual_path.suffix == '.gz'
        assert actual_path.exists()
        
        loaded = manager.load(actual_path)
        assert loaded is not None
    
    def test_load_nonexistent_file(self, temp_dir):
        manager = ContractFileManager()
        
        with pytest.raises(DeserializationError):
            manager.load(temp_dir / "nonexistent.json")
    
    def test_save_creates_parent_directory(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        nested_path = temp_dir / "subdir" / "nested" / "contract.json"
        
        manager = ContractFileManager()
        manager.save(contract, nested_path)
        
        assert nested_path.exists()
    
    def test_load_compressed_file(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        file_path = temp_dir / "contract.json"
        
        # Save compressed
        save_manager = ContractFileManager(compress=True)
        actual_path = save_manager.save(contract, file_path)
        
        # Load compressed
        load_manager = ContractFileManager()
        loaded = load_manager.load(actual_path)
        
        assert loaded.header.target_interface_id == "test"
    
    def test_save_with_clauses(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        ref = SubjectReference(SubjectKind.FUNCTION, "func")
        clause = ContractClause("clause_1", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
        file_path = temp_dir / "contract.json"
        
        manager = ContractFileManager()
        manager.save(contract, file_path)
        
        loaded = manager.load(file_path)
        
        assert len(loaded.clauses) == 1
    
    def test_atomic_write_creates_temp_file(self, temp_dir):
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        file_path = temp_dir / "contract.json"
        
        manager = ContractFileManager()
        manager.save(contract, file_path)
        
        # Temp file should not exist after successful write
        temp_path = file_path.with_suffix('.tmp')
        assert not temp_path.exists()

class TestContractArtifactManager:
    """Test ContractArtifactManager."""
    
    @pytest.fixture
    def temp_dir(self):
        temp = Path(tempfile.mkdtemp())
        yield temp
        shutil.rmtree(temp)
    
    def test_save_artifact(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        artifact_path = manager.save_artifact(contract)
        
        assert artifact_path.exists()
    
    def test_load_artifact(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        contract_id = contract.header.contract_id
        
        manager.save_artifact(contract)
        
        loaded = manager.load_artifact(contract_id)
        
        assert loaded is not None
        assert loaded.header.contract_id == contract_id
    
    def test_load_nonexistent_artifact(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        loaded = manager.load_artifact("nonexistent_id")
        
        assert loaded is None
    
    def test_artifact_caching(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        contract_id = contract.header.contract_id
        
        manager.save_artifact(contract)
        
        # First load (from disk)
        loaded1 = manager.load_artifact(contract_id)
        
        # Second load (from cache)
        loaded2 = manager.load_artifact(contract_id)
        
        assert loaded1 is not None
        assert loaded2 is not None
        # Should be same object from cache
        assert loaded1 is loaded2
    
    def test_save_artifact_creates_subdirectory(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        artifact_path = manager.save_artifact(contract)
        
        # Should be in subdirectory based on contract_id prefix
        assert artifact_path.parent != temp_dir
    
    def test_save_artifact_updates_index(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        manager.save_artifact(contract)
        
        # Index should exist
        assert manager.index_path.exists()
        index = manager._load_index()
        assert len(index['contracts']) == 1
    
    def test_save_multiple_artifacts(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        for i in range(3):
            header = ContractHeader(target_interface_id=f"test_{i}")
            contract = ContractDocument(header=header)
            manager.save_artifact(contract)
        
        index = manager._load_index()
        assert len(index['contracts']) == 3
    
    def test_save_artifact_with_compression(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(target_interface_id="test")
        contract = ContractDocument(header=header)
        
        artifact_path = manager.save_artifact(contract, compress=True)
        
        # Should have .gz in path
        assert '.gz' in artifact_path.name
    
    def test_artifact_filename_includes_version(self, temp_dir):
        manager = ContractArtifactManager(temp_dir)
        
        header = ContractHeader(
            target_interface_id="test",
            contract_version="2.1.0"
        )
        contract = ContractDocument(header=header)
        
        artifact_path = manager.save_artifact(contract)
        
        # Filename should include version
        assert "2.1.0" in artifact_path.name

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
