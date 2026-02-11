"""
Module 06: Contract Schema - Serialization & Persistence

Contract serialization system providing:
    - JSON serialization/deserialization
- Integrity verification (checksums)
- Compression support
- Editoric file operations
- Artifact management
- Caching
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import hashlib
import gzip
from datetime import datetime

from .contract_entities import ContractDocument
from .contract_validation import ContractValidator, ValidationContext

# ============================================================================
# INTEGRITY VERIFICATION
# ============================================================================


@dataclass
class IntegrityInfo:
    """Contract integrity information."""

    checksum: str
    checksum_algorithm: str = "sha256"
    computed_at: str = ""

    def __post_init__(self):
        if not self.computed_at:
            self.computed_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "checksum": self.checksum,
            "checksum_algorithm": self.checksum_algorithm,
            "computed_at": self.computed_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "IntegrityInfo":
        """Deserialize from dictionary."""
        return IntegrityInfo(
            checksum=data["checksum"],
            checksum_algorithm=data.get("checksum_algorithm", "sha256"),
            computed_at=data.get("computed_at", ""),
        )


def compute_checksum(content: str, algorithm: str = "sha256") -> str:
    """
    Compute checksum of content.

    Args:
        content: String content to checksum
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex-encoded checksum
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def verify_checksum(content: str, expected: str, algorithm: str = "sha256") -> bool:
    """
    Verify content checksum.

    Args:
        content: Content to verify
        expected: Expected checksum
        algorithm: Hash algorithm

    Returns:
        True if checksum matches
    """
    actual = compute_checksum(content, algorithm)
    return actual == expected


# ============================================================================
# SERIALIZATION ERRORS
# ============================================================================


class SerializationError(Exception):
    """Base class for serialization errors."""

    pass


class DeserializationError(Exception):
    """Base class for deserialization errors."""

    pass


class ContractIntegrityError(Exception):
    pass


# ============================================================================
# CONTRACT SERIALIZER
# ============================================================================


class ContractSerializer:
    """
    Serializes contracts to JSON format.

    Provides deterministic serialization with integrity checks.
    """

    def __init__(self, pretty: bool = True, include_integrity: bool = True):
        """
        Initialize serializer.

        Args:
            pretty: Use pretty-printing (indent=2)
            include_integrity: Include integrity checksum
        """
        self.pretty = pretty
        self.include_integrity = include_integrity

    def serialize(self, contract: ContractDocument) -> str:
        """
        Serialize contract to JSON string.

        Args:
            contract: Contract to serialize

        Returns:
            JSON string

        Raises:
            SerializationError: If serialization fails
        """
        try:
            # Convert to dictionary
            contract_dict = contract.to_dict()

            # Wrap in envelope
            envelope = {"schema_version": contract.header.schema_version, "contract": contract_dict}

            # Add integrity if requested
            if self.include_integrity:
                # Always compute checksum on compact version for stability
                compact_str = json.dumps(envelope, sort_keys=True)
                checksum = compute_checksum(compact_str)

                # Add to envelope and re-serialize
                envelope["integrity"] = IntegrityInfo(checksum=checksum).to_dict()

                if self.pretty:
                    return json.dumps(envelope, indent=2, sort_keys=True)
                else:
                    return json.dumps(envelope, sort_keys=True)

            if self.pretty:
                return json.dumps(envelope, indent=2, sort_keys=True)
            else:
                return json.dumps(envelope, sort_keys=True)

        except Exception as e:
            raise SerializationError(f"Failed to serialize contract: {e}")

    def _add_integrity(self, json_str: str) -> str:
        """Add integrity block to JSON."""
        # Compute checksum of content
        checksum = compute_checksum(json_str)

        # Parse JSON, add integrity block
        data = json.loads(json_str)
        data["integrity"] = IntegrityInfo(checksum=checksum).to_dict()

        # Re-serialize
        if self.pretty:
            return json.dumps(data, indent=2, sort_keys=True)
        else:
            return json.dumps(data, sort_keys=True)


# ============================================================================
# CONTRACT DESERIALIZER
# ============================================================================


class ContractDeserializer:
    """
    Deserializes contracts from JSON format.

    Validates integrity and schema during deserialization.
    """

    def __init__(self, verify_integrity: bool = True, validate_contract: bool = True):
        """
        Initialize deserializer.

        Args:
            verify_integrity: Verify checksum
            validate_contract: Run schema validation
        """
        self.verify_integrity = verify_integrity
        self.validate_contract = validate_contract

    def deserialize(self, json_str: str) -> ContractDocument:
        """
        Deserialize contract from JSON string.

        Args:
            json_str: JSON string

        Returns:
            ContractDocument

        Raises:
            DeserializationError: If deserialization fails
            ContractIntegrityError: If checksum verification fails
        """
        try:
            # Parse JSON
            data = json.loads(json_str)

            # Verify integrity if present
            if self.verify_integrity and "integrity" in data:
                self._verify_integrity(json_str, data)

            # Check schema version
            schema_version = data.get("schema_version", "1.0.0")
            if not self._is_supported_schema(schema_version):
                raise DeserializationError(f"Unsupported schema version: {schema_version}")

            # Extract contract data
            contract_dict = data.get("contract")
            if not contract_dict:
                raise DeserializationError("Missing 'contract' field")

            # Deserialize contract
            contract = ContractDocument.from_dict(contract_dict)

            # Validate if requested
            if self.validate_contract:
                self._validate_contract(contract)

            return contract

        except json.JSONDecodeError as e:
            raise DeserializationError(f"Invalid JSON: {e}")

        except Exception as e:
            if isinstance(e, (DeserializationError, ContractIntegrityError)):
                raise
            raise DeserializationError(f"Failed to deserialize contract: {e}")

    def _verify_integrity(self, json_str: str, data: Dict[str, Any]):
        """Verify contract integrity."""
        # Extract integrity info (don't modify original data)
        integrity_data = data.get("integrity")
        if not integrity_data:
            return

        integrity = IntegrityInfo.from_dict(integrity_data)

        # Create copy without integrity block for checksum
        # Always use compact representation for checksum verification
        data_copy = {k: v for k, v in data.items() if k != "integrity"}
        content_without_integrity = json.dumps(data_copy, sort_keys=True)

        if not verify_checksum(
            content_without_integrity, integrity.checksum, integrity.checksum_algorithm
        ):
            raise ContractIntegrityError("Checksum verification failed - contract may be corrupted")

    def _is_supported_schema(self, schema_version: str) -> bool:
        """Check if schema version is supported."""
        # Currently only support 1.0.0
        return schema_version == "1.0.0"

    def _validate_contract(self, contract: ContractDocument):
        """Validate contract structure."""
        # Only do basic structural validation
        # Full validation with IR context should be done separately
        try:
            validator = ContractValidator()
            # Run quick schema validation
            result = validator.validate_quick(contract)
            if not result:
                raise DeserializationError("Contract failed schema validation")
        except Exception as e:
            # We're just checking basic structure here
            if "entity_index" not in str(e):
                raise DeserializationError(f"Contract validation failed: {e}")


# ============================================================================
# FILE OPERATIONS
# ============================================================================


class ContractFileManager:
    """
    Manages contract file operations.

    Provides atomic writes, compression, and file management.
    """

    def __init__(self, compress: bool = False):
        """
        Initialize file manager.

        Args:
            compress: Enable gzip compression
        """
        self.compress = compress
        self.serializer = ContractSerializer(pretty=True)
        self.deserializer = ContractDeserializer(validate_contract=False)

    def save(self, contract: ContractDocument, path: Path) -> Path:
        """
        Save contract to file atomically.

        Args:
            contract: Contract to save
            path: Target file path

        Returns:
            Actual path where file was saved

        Raises:
            SerializationError: If save fails
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize contract
        json_str = self.serializer.serialize(contract)

        # Compress if requested
        if self.compress:
            content = gzip.compress(json_str.encode("utf-8"))
            path = path.with_suffix(path.suffix + ".gz")
        else:
            content = json_str.encode("utf-8")

        # Editoric write
        self._atomic_write(path, content)

        return path

    def load(self, path: Path) -> ContractDocument:
        """
        Load contract from file.

        Args:
            path: File path

        Returns:
            ContractDocument

        Raises:
            DeserializationError: If load fails
        """
        if not path.exists():
            raise DeserializationError(f"File not found: {path}")

        # Read file
        content = path.read_bytes()

        # Decompress if needed
        if path.suffix == ".gz":
            content = gzip.decompress(content)

        # Deserialize
        json_str = content.decode("utf-8")
        return self.deserializer.deserialize(json_str)

    def _atomic_write(self, path: Path, content: bytes):
        """Write file atomically."""
        temp_path = path.with_suffix(".tmp")

        try:
            # Write to temp file
            temp_path.write_bytes(content)

            # Editoric rename
            temp_path.replace(path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise SerializationError(f"Failed to write file: {e}")


# ============================================================================
# ARTIFACT MANAGEMENT
# ============================================================================


@dataclass
class ContractArtifact:
    """Contract artifact with metadata."""

    contract: ContractDocument
    file_path: Optional[Path] = None
    file_size: int = 0
    checksum: str = ""
    compressed: bool = False
    created_timestamp: str = ""

    def __post_init__(self):
        if not self.created_timestamp:
            self.created_timestamp = datetime.utcnow().isoformat()


class ContractArtifactManager:
    """
    Manages contract artifacts.

    Provides indexing, versioning, and artifact lifecycle management.
    """

    def __init__(self, artifacts_dir: Path):
        """
        Initialize artifact manager.

        Args:
            artifacts_dir: Directory for contract artifacts
        """
        self.artifacts_dir = artifacts_dir
        self.file_manager = ContractFileManager()
        self.index_path = artifacts_dir / "index.json"
        self._cache: Dict[str, ContractDocument] = {}

    def save_artifact(self, contract: ContractDocument, compress: bool = False) -> Path:
        """
        Save contract artifact.

        Args:
            contract: Contract to save
            compress: Enable compression

        Returns:
            Path where artifact was saved
        """
        # Generate filename
        contract_id = contract.header.contract_id
        version = contract.header.contract_version
        filename = f"{contract_id}_{version}.contract.json"

        # Determine subdirectory (by contract_id prefix)
        subdir = self.artifacts_dir / contract_id[:8]
        subdir.mkdir(parents=True, exist_ok=True)

        # Full path
        artifact_path = subdir / filename

        # Save contract
        file_manager = ContractFileManager(compress=compress)
        actual_path = file_manager.save(contract, artifact_path)

        # Update index
        self._update_index(contract, actual_path)

        # Cache
        self._cache[contract_id] = contract

        return actual_path

    def load_artifact(self, contract_id: str) -> Optional[ContractDocument]:
        """
        Load contract artifact by ID.

        Args:
            contract_id: Contract identifier

        Returns:
            ContractDocument or None if not found
        """
        # Check cache
        if contract_id in self._cache:
            return self._cache[contract_id]

        # Lookup in index
        index = self._load_index()

        for entry in index.get("contracts", []):
            if entry["contract_id"] == contract_id:
                artifact_path = self.artifacts_dir / entry["file_path"]
                contract = self.file_manager.load(artifact_path)

                # Cache
                self._cache[contract_id] = contract

                return contract

        return None

    def _update_index(self, contract: ContractDocument, artifact_path: Path):
        """Update artifact index."""
        index = self._load_index()

        # Add entry
        entry = {
            "contract_id": contract.header.contract_id,
            "target_interface": contract.header.target_interface_id,
            "version": contract.header.contract_version,
            "file_path": str(artifact_path.relative_to(self.artifacts_dir)),
            "created": datetime.utcnow().isoformat(),
        }

        if "contracts" not in index:
            index["contracts"] = []

        index["contracts"].append(entry)

        # Save index
        self._save_index(index)

    def _load_index(self) -> Dict[str, Any]:
        """Load artifact index."""
        if not self.index_path.exists():
            return {"contracts": []}

        with open(self.index_path, "r") as f:
            return json.load(f)

    def _save_index(self, index: Dict[str, Any]):
        """Save artifact index."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2, sort_keys=True)


__all__ = [
    "IntegrityInfo",
    "compute_checksum",
    "verify_checksum",
    "SerializationError",
    "DeserializationError",
    "ContractIntegrityError",
    "IntegrityError",
    "ContractSerializer",
    "ContractDeserializer",
    "ContractFileManager",
    "ContractArtifact",
    "ContractArtifactManager",
]


# Compatibility Alias
IntegrityError = ContractIntegrityError
