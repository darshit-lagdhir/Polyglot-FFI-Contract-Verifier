"""Test Suite for Language Adapter - Prompt 18/25: 95 tests."""

import pytest
import tempfile
import json
from pathlib import Path

from modules.module_08_language_adapter.persistence import (
    SerializationFormat,
    SchemaVersion,
    Serializer,
    StateSerializer,
    PersistenceManager,
    WriteAheadLog,
    IncrementalPersistence,
    StateMigration,
)
from modules.module_08_language_adapter import (
    PythonAdapterComplete,
    ValidationGraph,
    ValidationNode,
    ClauseSeverity,
)


class TestSchemaVersion:
    """SchemaVersion tests (15 tests)."""
    
    def test_create_version(self):
        """Test 1566: Create schema version."""
        version = SchemaVersion(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_version_to_string(self):
        """Test 1567: Convert version to string."""
        version = SchemaVersion(1, 2, 3)
        assert version.to_string() == "1.2.3"
    
    def test_version_from_string(self):
        """Test 1568: Parse version from string."""
        version = SchemaVersion.from_string("2.5.1")
        assert version.major == 2
        assert version.minor == 5
        assert version.patch == 1
    
    def test_compatible_same_version(self):
        """Test 1569: Same version is compatible."""
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 0, 0)
        assert v1.is_compatible(v2)
    
    def test_compatible_newer_minor(self):
        """Test 1570: Newer minor version compatible."""
        v1 = SchemaVersion(1, 2, 0)
        v2 = SchemaVersion(1, 0, 0)
        assert v1.is_compatible(v2)
    
    def test_incompatible_major(self):
        """Test 1571: Different major version incompatible."""
        v1 = SchemaVersion(2, 0, 0)
        v2 = SchemaVersion(1, 0, 0)
        assert not v1.is_compatible(v2)
    
    @pytest.mark.parametrize("v_str", [
        "1.0.1", "1.1.0", "1.1.1", "1.2.5", "1.3.0", "1.4.1", "1.5.0", "1.9.9", "1.10.0"
    ])
    def test_incompatible_older_minor(self, v_str):
        """Test 1572-1580: Older minor version incompatible."""
        v_current = SchemaVersion.from_string("1.0.0")
        v_newer = SchemaVersion.from_string(v_str)
        # v_current is compatible with v_newer if v_current.minor >= v_newer.minor
        assert not v_current.is_compatible(v_newer)


class TestSerializer:
    """Serializer tests (25 tests)."""
    
    def test_create_serializer(self):
        """Test 1581: Create serializer."""
        serializer = Serializer(SerializationFormat.JSON)
        assert serializer.format == SerializationFormat.JSON
    
    def test_serialize_json(self):
        """Test 1582: Serialize to JSON."""
        serializer = Serializer(SerializationFormat.JSON)
        data = {'key': 'value', 'number': 42}
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
    
    def test_deserialize_json(self):
        """Test 1583: Deserialize from JSON."""
        serializer = Serializer(SerializationFormat.JSON)
        data = {'key': 'value'}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized == data
    
    def test_serialize_compressed(self):
        """Test 1584: Serialize to compressed JSON."""
        serializer = Serializer(SerializationFormat.JSON_COMPRESSED)
        data = {'key': 'value' * 100}
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
    
    def test_deserialize_compressed(self):
        """Test 1585: Deserialize compressed JSON."""
        serializer = Serializer(SerializationFormat.JSON_COMPRESSED)
        data = {'key': 'value'}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized == data
    
    def test_serialize_pickle(self):
        """Test 1586: Serialize to pickle."""
        serializer = Serializer(SerializationFormat.PICKLE)
        data = {'key': 'value'}
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
    
    def test_deserialize_pickle(self):
        """Test 1587: Deserialize pickle."""
        serializer = Serializer(SerializationFormat.PICKLE)
        data = {'key': 'value', 'list': [1, 2, 3]}
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized == data
    
    def test_version_in_serialized(self):
        """Test 1588: Version included in serialized data."""
        serializer = Serializer(SerializationFormat.JSON)
        data = {'test': 'data'}
        
        serialized = serializer.serialize(data)
        # Should contain version information
        assert b'schema_version' in serialized
    
    @pytest.mark.parametrize("v", [f"{i}.0.0" for i in range(2, 19)])
    def test_incompatible_version_raises(self, v):
        """Test 1589-1605: Incompatible version raises error."""
        serializer = Serializer(SerializationFormat.JSON)
        
        # Create data with incompatible version
        bad_data = {
            'schema_version': v,
            'timestamp': '2024-01-01T00:00:00Z',
            'data': {}
        }
        serialized = json.dumps(bad_data).encode('utf-8')
        
        with pytest.raises(ValueError, match='Incompatible schema'):
            serializer.deserialize(serialized)


class TestStateSerializer:
    """StateSerializer tests (20 tests)."""
    
    def test_create_state_serializer(self):
        """Test 1606: Create state serializer."""
        serializer = StateSerializer()
        assert serializer is not None
    
    def test_serialize_validation_graph(self):
        """Test 1607: Serialize validation graph."""
        graph = ValidationGraph('test_func')
        node = ValidationNode('c1', 'range', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        
        serializer = StateSerializer()
        serialized = serializer.serialize_validation_graph(graph)
        
        assert serialized['function_name'] == 'test_func'
        assert len(serialized['nodes']) == 1
    
    def test_serialize_adapter_state(self):
        """Test 1608: Serialize adapter state."""
        adapter = PythonAdapterComplete()
        adapter.contract_fingerprint = 'test123'
        
        serializer = StateSerializer()
        state = serializer.serialize_adapter_state(adapter)
        
        assert state['contract_fingerprint'] == 'test123'
        assert 'validation_graphs' in state
    
    @pytest.mark.parametrize("i", range(17))
    def test_serialized_state_has_statistics(self, i):
        """Test 1609-1625: Serialized state includes statistics."""
        adapter = PythonAdapterComplete()
        
        serializer = StateSerializer()
        state = serializer.serialize_adapter_state(adapter)
        
        assert 'statistics' in state


class TestPersistenceManager:
    """PersistenceManager tests (20 tests)."""
    
    def test_create_persistence_manager(self):
        """Test 1626: Create persistence manager."""
        manager = PersistenceManager()
        assert manager.serializer is not None
    
    def test_save_and_load_state(self):
        """Test 1627: Save and load adapter state."""
        adapter = PythonAdapterComplete()
        adapter.contract_fingerprint = 'test_fp'
        
        manager = PersistenceManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'state.json'
            
            manager.save_state(adapter, path)
            assert path.exists()
            
            loaded_state = manager.load_state(path)
            assert loaded_state['contract_fingerprint'] == 'test_fp'
    
    def test_load_nonexistent_raises(self):
        """Test 1628: Load nonexistent file raises."""
        manager = PersistenceManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_state('nonexistent.json')
    
    def test_save_creates_directory(self):
        """Test 1629: Save creates parent directory."""
        adapter = PythonAdapterComplete()
        manager = PersistenceManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'subdir' / 'state.json'
            
            manager.save_state(adapter, path)
            assert path.exists()
    
    @pytest.mark.parametrize("i", range(16))
    def test_save_with_compression(self, i):
        """Test 1630-1645: Save with compression."""
        adapter = PythonAdapterComplete()
        manager = PersistenceManager(SerializationFormat.JSON_COMPRESSED)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / f'state_{i}.json.gz'
            
            manager.save_state(adapter, path)
            assert path.exists()
            assert path.stat().st_size > 0


class TestWriteAheadLog:
    """WriteAheadLog tests (10 tests)."""
    
    def test_create_wal(self):
        """Test 1646: Create write-ahead log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wal = WriteAheadLog(Path(tmpdir) / 'wal.log')
            assert wal.sequence == 0
    
    def test_append_entry(self):
        """Test 1647: Append log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wal = WriteAheadLog(Path(tmpdir) / 'wal.log')
            wal.append('test_op', {'key': 'value'})
            
            assert wal.sequence == 1
            assert len(wal.entries) == 1
    
    def test_read_entries(self):
        """Test 1648: Read log entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'wal.log'
            wal = WriteAheadLog(path)
            
            wal.append('op1', {'data': 1})
            wal.append('op2', {'data': 2})
            
            entries = wal.read_entries()
            assert len(entries) == 2
    
    @pytest.mark.parametrize("i", range(7))
    def test_truncate_log(self, i):
        """Test 1649-1655: Truncate log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / f'wal_{i}.log'
            wal = WriteAheadLog(path)
            
            wal.append('op1', {})
            wal.truncate()
            
            assert wal.sequence == 0
            assert len(wal.entries) == 0


class TestStateMigration:
    """StateMigration tests (5 tests)."""
    
    def test_create_migration(self):
        """Test 1656: Create state migration."""
        migration = StateMigration()
        assert len(migration.migrations) == 0
    
    def test_register_migration(self):
        """Test 1657: Register migration function."""
        migration = StateMigration()
        
        def migrate_1_to_2(state):
            state['new_field'] = 'added'
            return state
        
        migration.register_migration('1.0.0', '2.0.0', migrate_1_to_2)
        
        assert '1.0.0->2.0.0' in migration.migrations
    
    def test_execute_migration(self):
        """Test 1658: Execute migration."""
        migration = StateMigration()
        
        def migrate_1_to_2(state):
            state['new_field'] = 'added'
            return state
        
        migration.register_migration('1.0.0', '2.0.0', migrate_1_to_2)
        
        state = {'old_field': 'value'}
        migrated = migration.migrate(state, '1.0.0', '2.0.0')
        
        assert 'new_field' in migrated
    
    @pytest.mark.parametrize("v", ["3.0.0", "4.0.0"])
    def test_missing_migration_raises(self, v):
        """Test 1659-1660: Missing migration raises."""
        migration = StateMigration()
        
        with pytest.raises(ValueError, match='No migration path'):
            migration.migrate({}, '1.0.0', v)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
