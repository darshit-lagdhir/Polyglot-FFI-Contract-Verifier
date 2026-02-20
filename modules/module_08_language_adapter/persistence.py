# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 3d4c0bd8ad151494
# ==============================================================================

"""Serialization and state persistence for Language Adapter."""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import json
import pickle
import gzip


# ════════════════════════════════════════════════════════════════════════════
# SECTION 99: SERIALIZATION FORMAT
# ════════════════════════════════════════════════════════════════════════════

class SerializationFormat(Enum):
    """Serialization format options."""
    JSON = "json"
    JSON_COMPRESSED = "json.gz"
    PICKLE = "pickle"
    PICKLE_COMPRESSED = "pickle.gz"


@dataclass
class SchemaVersion:
    """Schema version information."""
    
    major: int
    minor: int
    patch: int
    
    def to_string(self) -> str:
        """Convert to version string."""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @staticmethod
    def from_string(version_str: str) -> 'SchemaVersion':
        """Parse version string."""
        parts = version_str.split('.')
        return SchemaVersion(
            major=int(parts[0]),
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )
    
    def is_compatible(self, other: 'SchemaVersion') -> bool:
        """Check if version is compatible with another."""
        # Major version must match
        if self.major != other.major:
            return False
        # Minor version must be same or older
        if self.minor < other.minor:
            return False
        # If minor same, patch must be same or older
        if self.minor == other.minor and self.patch < other.patch:
            return False
        return True


# ════════════════════════════════════════════════════════════════════════════
# SECTION 100: SERIALIZER
# ════════════════════════════════════════════════════════════════════════════

class Serializer:
    """
    Multi-format serialization engine.
    
    Supports JSON, Pickle, and compressed variants.
    """
    
    CURRENT_VERSION = SchemaVersion(1, 0, 0)
    
    def __init__(self, format: SerializationFormat = SerializationFormat.JSON):
        self.format = format
    
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """
        Serialize data to bytes.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized bytes
        """
        # Add version information
        versioned_data = {
            'schema_version': self.CURRENT_VERSION.to_string(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': data
        }
        
        if self.format == SerializationFormat.JSON:
            return json.dumps(versioned_data, indent=2).encode('utf-8')
        
        elif self.format == SerializationFormat.JSON_COMPRESSED:
            json_bytes = json.dumps(versioned_data).encode('utf-8')
            return gzip.compress(json_bytes)
        
        elif self.format == SerializationFormat.PICKLE:
            return pickle.dumps(versioned_data)
        
        elif self.format == SerializationFormat.PICKLE_COMPRESSED:
            pickle_bytes = pickle.dumps(versioned_data)
            return gzip.compress(pickle_bytes)
        
        else:
            raise ValueError(f"Unsupported format: {self.format}")
    
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """
        Deserialize bytes to data.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized data
            
        Raises:
            ValueError: If schema version incompatible
        """
        if self.format == SerializationFormat.JSON:
            versioned_data = json.loads(data.decode('utf-8'))
        
        elif self.format == SerializationFormat.JSON_COMPRESSED:
            json_bytes = gzip.decompress(data)
            versioned_data = json.loads(json_bytes.decode('utf-8'))
        
        elif self.format == SerializationFormat.PICKLE:
            versioned_data = pickle.loads(data)
        
        elif self.format == SerializationFormat.PICKLE_COMPRESSED:
            pickle_bytes = gzip.decompress(data)
            versioned_data = pickle.loads(pickle_bytes)
        
        else:
            raise ValueError(f"Unsupported format: {self.format}")
        
        # Validate schema version
        version_str = versioned_data.get('schema_version', '0.0.0')
        version = SchemaVersion.from_string(version_str)
        
        if not self.CURRENT_VERSION.is_compatible(version):
            raise ValueError(
                f"Incompatible schema version: {version_str} "
                f"(current: {self.CURRENT_VERSION.to_string()})"
            )
        
        return versioned_data['data']


# ════════════════════════════════════════════════════════════════════════════
# SECTION 101: STATE SERIALIZER
# ════════════════════════════════════════════════════════════════════════════

class StateSerializer:
    """
    Serializes complete adapter state.
    
    Converts runtime objects to serializable dictionaries.
    """
    
    def serialize_ownership_graph(
        self,
        ownership_graph: Any
    ) -> Dict[str, Any]:
        """
        Serialize ownership graph.
        
        Args:
            ownership_graph: OwnershipGraph instance
            
        Returns:
            Serialized graph data
        """
        allocations = []
        
        # Access allocations safely (assume dict-like)
        allocs = getattr(ownership_graph, 'allocations', {})
        for address, alloc_data in allocs.items():
            serialized_alloc = {
                'address': address,
                'size': alloc_data.get('size', 0),
                'state': str(alloc_data.get('state', 'unknown')),
                'allocated_at': alloc_data.get('allocated_at'),
                'history': alloc_data.get('history', [])
            }
            # Unpack state value if it's an enum
            if hasattr(alloc_data.get('state'), 'value'):
                serialized_alloc['state'] = alloc_data['state'].value
                
            allocations.append(serialized_alloc)
        
        edges = getattr(ownership_graph, 'ownership_edges', {})
        counts = getattr(ownership_graph, 'ref_counts', {})
        
        return {
            'allocations': allocations,
            'ownership_edges': {
                str(k): v for k, v in edges.items()
            },
            'ref_counts': {
                str(k): v for k, v in counts.items()
            }
        }
    
    def serialize_validation_graph(
        self,
        graph: Any
    ) -> Dict[str, Any]:
        """
        Serialize validation graph.
        
        Args:
            graph: ValidationGraph instance
            
        Returns:
            Serialized graph data
        """
        nodes = []
        
        gnodes = getattr(graph, 'nodes', [])
        for node in gnodes:
            serialized_node = {
                'clause_id': getattr(node, 'clause_id', ''),
                'clause_type': getattr(node, 'clause_type', ''),
                'severity': str(getattr(node, 'severity', '')),
                'parameters': getattr(node, 'parameters', {}),
                'failure_message': getattr(node, 'failure_message', '')
            }
            if hasattr(node, 'severity') and hasattr(node.severity, 'value'):
                serialized_node['severity'] = node.severity.value
                
            nodes.append(serialized_node)
        
        return {
            'function_name': getattr(graph, 'function_name', 'unknown'),
            'nodes': nodes
        }
    
    def serialize_configuration(
        self,
        config: Any
    ) -> Dict[str, Any]:
        """
        Serialize adapter configuration.
        
        Args:
            config: AdapterConfiguration instance
            
        Returns:
            Serialized configuration
        """
        if hasattr(config, 'to_dict'):
            return config.to_dict()
        
        return {
            'verbose_logging': getattr(config, 'verbose_logging', False),
            'trace_validation': getattr(config, 'trace_validation', False),
            'mode': str(getattr(config, 'mode', 'default'))
        }
    
    def serialize_adapter_state(
        self,
        adapter: Any
    ) -> Dict[str, Any]:
        """
        Serialize complete adapter state.
        
        Args:
            adapter: LanguageAdapter instance
            
        Returns:
            Serialized adapter state
        """
        state = {
            'contract_fingerprint': getattr(adapter, 'contract_fingerprint', ''),
            'validation_graphs': {},
            'configuration': None,
            'statistics': adapter.get_statistics() if hasattr(adapter, 'get_statistics') else {}
        }
        
        # Serialize validation graphs
        vgraphs = getattr(adapter, 'validation_graphs', {})
        for func_name, graph in vgraphs.items():
            state['validation_graphs'][func_name] = self.serialize_validation_graph(graph)
        
        # Serialize configuration
        config = getattr(adapter, 'config', None)
        if config:
            state['configuration'] = self.serialize_configuration(config)
        
        # Serialize ownership if available
        registry = getattr(adapter, 'ownership_registry', None)
        if registry:
            state['ownership'] = self.serialize_ownership_graph(registry)
        
        return state


# ════════════════════════════════════════════════════════════════════════════
# SECTION 102: PERSISTENCE MANAGER
# ════════════════════════════════════════════════════════════════════════════

class PersistenceManager:
    """
    Manages state persistence operations.
    
    Handles save/load of adapter state with multiple formats.
    """
    
    def __init__(
        self,
        format: SerializationFormat = SerializationFormat.JSON
    ):
        self.serializer = Serializer(format)
        self.state_serializer = StateSerializer()
    
    def save_state(
        self,
        adapter: Any,
        path: Union[str, Path]
    ) -> None:
        """
        Save adapter state to file.
        
        Args:
            adapter: LanguageAdapter instance
            path: File path to save to
        """
        # Serialize adapter state
        state_data = self.state_serializer.serialize_adapter_state(adapter)
        
        # Serialize to bytes
        serialized = self.serializer.serialize(state_data)
        
        # Write to file
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(serialized)
    
    def load_state(
        self,
        path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Load adapter state from file.
        
        Args:
            path: File path to load from
            
        Returns:
            Deserialized state data
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")
        
        # Read file
        with open(path, 'rb') as f:
            serialized = f.read()
        
        # Deserialize
        return self.serializer.deserialize(serialized)
    
    def save_snapshot(
        self,
        snapshot: Any,
        path: Union[str, Path]
    ) -> None:
        """
        Save state snapshot to file.
        
        Args:
            snapshot: StateSnapshot instance
            path: File path
        """
        snapshot_data = snapshot.to_dict() if hasattr(snapshot, 'to_dict') else snapshot
        serialized = self.serializer.serialize(snapshot_data)
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(serialized)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 103: INCREMENTAL PERSISTENCE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class LogEntry:
    """Write-ahead log entry."""
    
    sequence: int
    timestamp: str
    operation: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sequence': self.sequence,
            'timestamp': self.timestamp,
            'operation': self.operation,
            'data': self.data
        }


class WriteAheadLog:
    """
    Write-ahead log for incremental persistence.
    
    Records state changes as log entries.
    """
    
    def __init__(self, log_path: Union[str, Path]):
        self.log_path = Path(log_path)
        self.sequence = 0
        self.entries: List[LogEntry] = []
    
    def append(
        self,
        operation: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Append log entry.
        
        Args:
            operation: Operation name
            data: Operation data
        """
        entry = LogEntry(
            sequence=self.sequence,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            operation=operation,
            data=data
        )
        
        self.entries.append(entry)
        self.sequence += 1
        
        # Write to file
        self._write_entry(entry)
    
    def _write_entry(self, entry: LogEntry) -> None:
        """Write entry to log file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
    
    def read_entries(self) -> List[LogEntry]:
        """Read all log entries."""
        if not self.log_path.exists():
            return []
        
        entries = []
        
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Handle LogEntry constructor
                    entry = LogEntry(
                        sequence=data['sequence'],
                        timestamp=data['timestamp'],
                        operation=data['operation'],
                        data=data['data']
                    )
                    entries.append(entry)
        
        return entries
    
    def truncate(self) -> None:
        """Truncate log file."""
        if self.log_path.exists():
            self.log_path.unlink()
        self.entries.clear()
        self.sequence = 0


class IncrementalPersistence:
    """
    Incremental persistence using write-ahead log.
    
    Combines periodic snapshots with continuous logging.
    """
    
    def __init__(
        self,
        snapshot_path: Union[str, Path],
        log_path: Union[str, Path],
        snapshot_interval: int = 100
    ):
        self.snapshot_path = Path(snapshot_path)
        self.log_path = Path(log_path)
        self.snapshot_interval = snapshot_interval
        self.persistence_manager = PersistenceManager()
        self.wal = WriteAheadLog(log_path)
        self.operation_count = 0
    
    def record_operation(
        self,
        operation: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Record state-changing operation.
        
        Args:
            operation: Operation name
            data: Operation data
        """
        self.wal.append(operation, data)
        self.operation_count += 1
    
    def should_snapshot(self) -> bool:
        """Check if snapshot should be taken."""
        return self.operation_count >= self.snapshot_interval
    
    def take_snapshot(self, adapter: Any) -> None:
        """
        Take state snapshot.
        
        Args:
            adapter: Adapter instance
        """
        self.persistence_manager.save_state(adapter, self.snapshot_path)
        
        # Truncate WAL after snapshot
        self.wal.truncate()
        self.operation_count = 0
    
    def restore_state(self) -> Optional[Dict[str, Any]]:
        """
        Restore state from snapshot and log.
        
        Returns:
            Restored state or None
        """
        # Load snapshot if exists
        if not self.snapshot_path.exists():
            return None
        
        state = self.persistence_manager.load_state(self.snapshot_path)
        
        # Replay log entries
        entries = self.wal.read_entries()
        for entry in entries:
            # Apply operation to state (this logic depends on integration)
            pass
        
        return state


# ════════════════════════════════════════════════════════════════════════════
# SECTION 104: STATE MIGRATION
# ════════════════════════════════════════════════════════════════════════════

class StateMigration:
    """
    Migrates state between schema versions.
    
    Provides transformation functions for version upgrades.
    """
    
    def __init__(self):
        self.migrations: Dict[str, Callable] = {}
    
    def register_migration(
        self,
        from_version: str,
        to_version: str,
        migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Register migration function.
        
        Args:
            from_version: Source version
            to_version: Target version
            migration_func: Migration function
        """
        key = f"{from_version}->{to_version}"
        self.migrations[key] = migration_func
    
    def migrate(
        self,
        state: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        Migrate state between versions.
        
        Args:
            state: State to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migrated state
        """
        key = f"{from_version}->{to_version}"
        
        if key not in self.migrations:
            raise ValueError(f"No migration path: {key}")
        
        migration_func = self.migrations[key]
        return migration_func(state)


# Export all persistence components
__all__ = [
    'SerializationFormat',
    'SchemaVersion',
    'Serializer',
    'StateSerializer',
    'PersistenceManager',
    'LogEntry',
    'WriteAheadLog',
    'IncrementalPersistence',
    'StateMigration',
]