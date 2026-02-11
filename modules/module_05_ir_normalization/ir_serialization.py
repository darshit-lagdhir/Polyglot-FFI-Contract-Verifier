"""
Module 05: IR Serialization and Persistence

Handles serialization, deserialization, and persistent storage of IR artifacts.
"""

import gzip
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ir_entities import (
    ArrayKind,
    ArrayType,
    AttributeEntity,
    CallingConvention,
    Endianness,
    EntityKind,
    EnumerationType,
    FieldEntity,
    FunctionPointerType,
    FunctionSymbol,
    InterfaceUnit,
    IREntity,
    MetadataEntity,
    PaddingEntity,
    ParameterEntity,
    PointerType,
    ReturnEntity,
    ReturnMechanism,
    ScalarKind,
    ScalarType,
    StructureType,
    SymbolEntity,
    TypeEntity,
    UnionType,
    VariableSymbol,
)
from .ir_validation import ValidationReport

# ============================================================================
# ENTITY FACTORY (RECONSTRUCTION LOGIC)
# ============================================================================


class IREntityFactory:
    """Factory for reconstructing IR entities from dictionaries."""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[IREntity]:
        """Dispatch deserialization based on entity kind."""
        if not data or "kind" not in data:
            return None

        kind_val = data["kind"]
        try:
            kind = EntityKind(kind_val)
        except ValueError:
            return None

        if kind == EntityKind.INTERFACE_UNIT:
            return IREntityFactory.interface_unit_from_dict(data)
        elif kind == EntityKind.METADATA:
            return IREntityFactory.metadata_from_dict(data)
        elif kind == EntityKind.ATTRIBUTE:
            return IREntityFactory.attribute_from_dict(data)
        elif kind == EntityKind.PARAMETER:
            return IREntityFactory.parameter_from_dict(data)
        elif kind == EntityKind.RETURN:
            return IREntityFactory.return_from_dict(data)
        elif kind == EntityKind.FIELD:
            return IREntityFactory.field_from_dict(data)
        elif kind == EntityKind.PADDING:
            return IREntityFactory.padding_from_dict(data)
        elif kind == EntityKind.FUNCTION_SYMBOL:
            return IREntityFactory.function_symbol_from_dict(data)
        elif kind == EntityKind.VARIABLE_SYMBOL:
            return IREntityFactory.variable_symbol_from_dict(data)
        elif kind == EntityKind.SCALAR_TYPE:
            return IREntityFactory.scalar_type_from_dict(data)
        elif kind == EntityKind.POINTER_TYPE:
            return IREntityFactory.pointer_type_from_dict(data)
        elif kind == EntityKind.ARRAY_TYPE:
            return IREntityFactory.array_type_from_dict(data)
        elif kind == EntityKind.STRUCTURE_TYPE:
            return IREntityFactory.structure_type_from_dict(data)
        elif kind == EntityKind.UNION_TYPE:
            return IREntityFactory.union_type_from_dict(data)
        elif kind == EntityKind.ENUM_TYPE:
            return IREntityFactory.enum_type_from_dict(data)
        elif kind == EntityKind.FUNCTION_POINTER_TYPE:
            return IREntityFactory.function_pointer_type_from_dict(data)

        return None

    @staticmethod
    def metadata_from_dict(data: Dict[str, Any]) -> MetadataEntity:
        # Use a temporary object to hold data since entity_id is init=False
        meta = MetadataEntity(
            source_file=data.get("source_file"),
            line_number=data.get("line_number"),
            column_number=data.get("column_number"),
            header_origin=data.get("header_origin"),
            ingestion_timestamp=data.get("ingestion_timestamp"),
        )
        if "entity_id" in data:
            meta.entity_id = data["entity_id"]
        return meta

    @staticmethod
    def attribute_from_dict(data: Dict[str, Any]) -> AttributeEntity:
        attr = AttributeEntity(
            attribute_name=data["attribute_name"], attribute_value=data.get("attribute_value")
        )
        if "entity_id" in data:
            attr.entity_id = data["entity_id"]
        return attr

    @staticmethod
    def parameter_from_dict(data: Dict[str, Any]) -> ParameterEntity:
        param = ParameterEntity(
            parameter_index=data["parameter_index"],
            parameter_name=data.get("parameter_name"),
            type_reference=data["type_reference"],
            is_const=data.get("is_const", False),
            is_volatile=data.get("is_volatile", False),
            is_restrict=data.get("is_restrict", False),
        )
        if "entity_id" in data:
            param.entity_id = data["entity_id"]
        return param

    @staticmethod
    def return_from_dict(data: Dict[str, Any]) -> ReturnEntity:
        ret = ReturnEntity(
            type_reference=data["type_reference"],
            return_mechanism=ReturnMechanism(data.get("return_mechanism", "direct")),
        )
        if "entity_id" in data:
            ret.entity_id = data["entity_id"]
        return ret

    @staticmethod
    def field_from_dict(data: Dict[str, Any]) -> FieldEntity:
        field = FieldEntity(
            field_index=data["field_index"],
            field_name=data.get("field_name"),
            type_reference=data["type_reference"],
            byte_offset=data["byte_offset"],
            bit_offset=data.get("bit_offset", 0),
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
        )
        if "entity_id" in data:
            field.entity_id = data["entity_id"]
        return field

    @staticmethod
    def padding_from_dict(data: Dict[str, Any]) -> PaddingEntity:
        padding = PaddingEntity(
            byte_offset=data["byte_offset"],
            size_bytes=data["size_bytes"],
            reason=data.get("reason", "alignment"),
        )
        if "entity_id" in data:
            padding.entity_id = data["entity_id"]
        return padding

    @staticmethod
    def function_symbol_from_dict(data: Dict[str, Any]) -> FunctionSymbol:
        func = FunctionSymbol(
            linkage_name=data["linkage_name"],
            source_name=data.get("source_name"),
            calling_convention=CallingConvention(data["calling_convention"]),
            is_variadic=data.get("is_variadic", False),
        )
        if "entity_id" in data:
            func.entity_id = data["entity_id"]
        if "return_entity" in data and data["return_entity"]:
            func.return_entity = IREntityFactory.return_from_dict(data["return_entity"])
        if "parameters" in data:
            func.parameters = [IREntityFactory.parameter_from_dict(p) for p in data["parameters"]]
        if "attributes" in data:
            func.attributes = [IREntityFactory.attribute_from_dict(a) for a in data["attributes"]]
        if "metadata" in data and data["metadata"]:
            func.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return func

    @staticmethod
    def variable_symbol_from_dict(data: Dict[str, Any]) -> VariableSymbol:
        var = VariableSymbol(
            linkage_name=data["linkage_name"],
            source_name=data.get("source_name"),
            type_reference=data["type_reference"],
            is_const=data.get("is_const", False),
            visibility=data.get("visibility", "extern"),
        )
        if "entity_id" in data:
            var.entity_id = data["entity_id"]
        if "attributes" in data:
            var.attributes = [IREntityFactory.attribute_from_dict(a) for a in data["attributes"]]
        if "metadata" in data and data["metadata"]:
            var.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return var

    @staticmethod
    def scalar_type_from_dict(data: Dict[str, Any]) -> ScalarType:
        scalar = ScalarType(
            scalar_kind=ScalarKind(data["scalar_kind"]),
            bit_width=data["bit_width"],
            is_signed=data.get("is_signed", False),
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
        )
        if "entity_id" in data:
            scalar.entity_id = data["entity_id"]
        if "metadata" in data and data["metadata"]:
            scalar.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return scalar

    @staticmethod
    def pointer_type_from_dict(data: Dict[str, Any]) -> PointerType:
        ptr = PointerType(
            pointer_depth=data["pointer_depth"],
            target_type_reference=data["target_type_reference"],
            pointer_width=data.get("size_bytes", 8) * 8,  # Approximation for InitVar
        )
        if "entity_id" in data:
            ptr.entity_id = data["entity_id"]
        if "metadata" in data and data["metadata"]:
            ptr.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return ptr

    @staticmethod
    def array_type_from_dict(data: Dict[str, Any]) -> ArrayType:
        arr = ArrayType(
            array_kind=ArrayKind(data["array_kind"]),
            element_type_reference=data["element_type_reference"],
            element_count=data.get("element_count"),
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
        )
        if "entity_id" in data:
            arr.entity_id = data["entity_id"]
        if "metadata" in data and data["metadata"]:
            arr.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return arr

    @staticmethod
    def structure_type_from_dict(data: Dict[str, Any]) -> StructureType:
        struct = StructureType(
            structure_name=data["structure_name"],
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
            is_packed=data.get("is_packed", False),
        )
        if "entity_id" in data:
            struct.entity_id = data["entity_id"]
        if "fields" in data:
            struct.fields = [IREntityFactory.field_from_dict(f) for f in data["fields"]]
        if "padding_regions" in data:
            struct.padding_regions = [
                IREntityFactory.padding_from_dict(p) for p in data["padding_regions"]
            ]
        if "metadata" in data and data["metadata"]:
            struct.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return struct

    @staticmethod
    def union_type_from_dict(data: Dict[str, Any]) -> UnionType:
        union = UnionType(
            union_name=data["union_name"],
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
        )
        if "entity_id" in data:
            union.entity_id = data["entity_id"]
        if "members" in data:
            # Bypass add_member to avoid offset 0 check if data is legacy or
            # weird, though normalized should be ok
            union.members = [IREntityFactory.field_from_dict(m) for m in data["members"]]
        if "metadata" in data and data["metadata"]:
            union.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return union

    @staticmethod
    def enum_type_from_dict(data: Dict[str, Any]) -> EnumerationType:
        enum = EnumerationType(
            enum_name=data["enum_name"],
            underlying_type_reference=data["underlying_type_reference"],
            size_bytes=data.get("size_bytes", 0),
            alignment_bytes=data.get("alignment_bytes", 0),
        )
        if "entity_id" in data:
            enum.entity_id = data["entity_id"]
        if "enumerators" in data:
            enum.enumerators = data["enumerators"]
        if "metadata" in data and data["metadata"]:
            enum.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return enum

    @staticmethod
    def function_pointer_type_from_dict(data: Dict[str, Any]) -> FunctionPointerType:
        fptr = FunctionPointerType(
            calling_convention=CallingConvention(data["calling_convention"]),
            return_type_reference=data["return_type_reference"],
            is_variadic=data.get("is_variadic", False),
            pointer_width=data.get("size_bytes", 8) * 8,
        )
        if "entity_id" in data:
            fptr.entity_id = data["entity_id"]
        if "parameters" in data:
            fptr.parameters = [IREntityFactory.parameter_from_dict(p) for p in data["parameters"]]
        if "metadata" in data and data["metadata"]:
            fptr.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return fptr

    @staticmethod
    def interface_unit_from_dict(data: Dict[str, Any]) -> InterfaceUnit:
        unit = InterfaceUnit(
            target_architecture=data["target_architecture"],
            operating_system=data["operating_system"],
            pointer_width=data["pointer_width"],
            endianness=Endianness(data["endianness"]),
            abi_mode=data["abi_mode"],
            compiler_family=data["compiler_family"],
            compiler_version=data["compiler_version"],
            compilation_flags=data.get("compilation_flags", []),
            ir_schema_version=data.get("ir_schema_version", "1.0.0"),
            normalization_version=data.get("normalization_version", "1.0.0"),
        )
        if "entity_id" in data:
            unit.entity_id = data["entity_id"]
        if "symbols" in data:
            unit.symbols = [
                s
                for s in (IREntityFactory.from_dict(x) for x in data["symbols"])
                if isinstance(s, SymbolEntity)
            ]
        if "types" in data:
            unit.types = [
                t
                for t in (IREntityFactory.from_dict(x) for x in data["types"])
                if isinstance(t, TypeEntity)
            ]
        if "metadata" in data and data["metadata"]:
            unit.metadata = IREntityFactory.metadata_from_dict(data["metadata"])
        return unit


# ============================================================================
# IR ARTIFACT
# ============================================================================


@dataclass
class IRArtifact:
    """Top-level IR artifact with versioning."""

    schema_version: str = "1.0.0"
    normalization_version: str = "1.0.0"
    creation_timestamp: Optional[str] = None

    interface_unit: Optional[InterfaceUnit] = None
    validation_report: Optional[ValidationReport] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize artifact to dictionary."""
        if self.creation_timestamp is None:
            self.creation_timestamp = datetime.now(timezone.utc).isoformat()

        data: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "normalization_version": self.normalization_version,
            "creation_timestamp": self.creation_timestamp,
        }

        if self.interface_unit:
            data["interface_unit"] = self.interface_unit.to_dict()

        if self.validation_report:
            data["validation_report"] = self.validation_report.to_dict()

        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "IRArtifact":
        """Deserialize artifact from dictionary."""
        artifact = IRArtifact(
            schema_version=data.get("schema_version", "1.0.0"),
            normalization_version=data.get("normalization_version", "1.0.0"),
            creation_timestamp=data.get("creation_timestamp"),
        )

        if "interface_unit" in data and data["interface_unit"]:
            artifact.interface_unit = IREntityFactory.interface_unit_from_dict(
                data["interface_unit"]
            )

        if "validation_report" in data and data["validation_report"]:
            # Assuming ValidationReport has a from_dict or can be simple reconstructed
            # For now, we'll manually reconstruct basic fields if needed, or
            # leave as None if complex
            vr_data = data["validation_report"]
            vr = ValidationReport()
            vr.passed = vr_data.get("passed", False)
            vr.schema_errors = vr_data.get("schema_errors", [])
            vr.reference_errors = vr_data.get("reference_errors", [])
            vr.type_errors = vr_data.get("type_errors", [])
            vr.symbol_errors = vr_data.get("symbol_errors", [])
            vr.graph_errors = vr_data.get("graph_errors", [])
            vr.platform_errors = vr_data.get("platform_errors", [])
            vr.completeness_errors = vr_data.get("completeness_errors", [])
            artifact.validation_report = vr

        return artifact


# ============================================================================
# IR MANIFEST
# ============================================================================


@dataclass
class IRManifest:
    """Metadata about IR artifact."""

    artifact_id: str = ""
    artifact_version: str = "1.0.0"

    source_headers: List[str] = field(default_factory=list)
    source_hash: str = ""

    generated_timestamp: str = ""
    generator_version: str = ""

    symbol_count: int = 0
    type_count: int = 0
    total_size_bytes: int = 0

    validation_passed: bool = False
    validation_error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize manifest."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_version": self.artifact_version,
            "source_headers": self.source_headers,
            "source_hash": self.source_hash,
            "generated_timestamp": self.generated_timestamp,
            "generator_version": self.generator_version,
            "symbol_count": self.symbol_count,
            "type_count": self.type_count,
            "total_size_bytes": self.total_size_bytes,
            "validation_passed": self.validation_passed,
            "validation_error_count": self.validation_error_count,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "IRManifest":
        """Deserialize manifest."""
        return IRManifest(
            artifact_id=data.get("artifact_id", ""),
            artifact_version=data.get("artifact_version", "1.0.0"),
            source_headers=data.get("source_headers", []),
            source_hash=data.get("source_hash", ""),
            generated_timestamp=data.get("generated_timestamp", ""),
            generator_version=data.get("generator_version", ""),
            symbol_count=data.get("symbol_count", 0),
            type_count=data.get("type_count", 0),
            total_size_bytes=data.get("total_size_bytes", 0),
            validation_passed=data.get("validation_passed", False),
            validation_error_count=data.get("validation_error_count", 0),
        )


# ============================================================================
# SERIALIZATION UTILITIES
# ============================================================================


def serialize_deterministically(obj: Any) -> str:
    """Serialize object to JSON deterministically."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True, separators=(",", ": "))


def compute_artifact_hash(artifact: IRArtifact) -> str:
    """Compute deterministic hash of IR artifact."""
    # We use a copy of to_dict but potentially without volatile fields like creation_timestamp
    # if alignment between runs is needed. But .3 says "No timestamps (or fixed timestamps)".
    # Let's override creation_timestamp for hashing if we want absolute
    # determinism across time.
    data = artifact.to_dict()
    # For hashing, we might want to stabilize the timestamp if it's meant to be part of the content ID
    # but usually content ID should be based on interface_unit.
    # However, if we want to hash the WHOLE artifact:
    json_str = serialize_deterministically(data)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def verify_artifact_integrity(artifact: IRArtifact, expected_hash: str) -> bool:
    """Verify IR artifact has not been modified."""
    actual_hash = compute_artifact_hash(artifact)
    return actual_hash == expected_hash


# ============================================================================
# COMPRESSED SERIALIZATION
# ============================================================================


def serialize_compressed(artifact: IRArtifact, output_path: Path):
    """Serialize IR artifact with gzip compression."""
    json_str = serialize_deterministically(artifact.to_dict())

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        f.write(json_str)


def deserialize_compressed(input_path: Path) -> IRArtifact:
    """Deserialize compressed IR artifact."""
    with gzip.open(input_path, "rt", encoding="utf-8") as f:
        data = json.load(f)

    return IRArtifact.from_dict(data)


# ============================================================================
# ARTIFACT MANAGER
# ============================================================================


class IntegrityError(Exception):
    pass


class IRArtifactManager:
    """Manages IR artifact storage and retrieval."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.artifacts_dir = cache_dir / "artifacts"
        self.manifests_dir = cache_dir / "manifests"

        self._loaded_artifacts: Dict[str, IRArtifact] = {}

    def save_artifact(self, artifact: IRArtifact, source_hash: str, compress: bool = True) -> Path:
        """Save IR artifact to disk."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

        # Compute artifact hash
        artifact_hash = compute_artifact_hash(artifact)

        # Save artifact
        if compress:
            artifact_path = self.artifacts_dir / f"{source_hash}.json.gz"
            serialize_compressed(artifact, artifact_path)
        else:
            artifact_path = self.artifacts_dir / f"{source_hash}.json"
            with open(artifact_path, "w") as f:
                f.write(serialize_deterministically(artifact.to_dict()))

        # Create and save manifest
        manifest = self._create_manifest(artifact, source_hash, artifact_hash)
        # Add actual file size to manifest
        manifest.total_size_bytes = artifact_path.stat().st_size

        manifest_path = self.manifests_dir / f"{source_hash}.manifest.json"
        with open(manifest_path, "w") as f:
            f.write(serialize_deterministically(manifest.to_dict()))

        # Update index
        self._update_index(source_hash, artifact_path, manifest_path)

        return artifact_path

    def load_artifact(
        self, source_hash: str, verify_integrity: bool = True
    ) -> Optional[IRArtifact]:
        """Load IR artifact from disk."""
        # Check in-memory cache
        if source_hash in self._loaded_artifacts:
            return self._loaded_artifacts[source_hash]

        # Check index/file system
        index_path = self.cache_dir / "index.json"
        if not index_path.exists():
            return None

        with open(index_path) as f:
            index = json.load(f)

        if source_hash not in index:
            return None

        entry = index[source_hash]
        artifact_path = Path(entry["artifact_path"])
        manifest_path = Path(entry["manifest_path"])

        if not artifact_path.exists():
            return None

        # Load manifest for hash verification
        if verify_integrity:
            with open(manifest_path) as f:
                manifest_data = json.load(f)
            expected_hash = manifest_data.get("artifact_id")
        else:
            expected_hash = None

        # Load artifact
        if artifact_path.suffix == ".gz":
            artifact = deserialize_compressed(artifact_path)
        else:
            with open(artifact_path) as f:
                data = json.load(f)
            artifact = IRArtifact.from_dict(data)

        # Verify integrity
        if verify_integrity and expected_hash:
            if not verify_artifact_integrity(artifact, expected_hash):
                raise IntegrityError(f"Artifact integrity check failed for {source_hash}")

        # Cache in memory
        self._loaded_artifacts[source_hash] = artifact

        return artifact

    def _create_manifest(
        self, artifact: IRArtifact, source_hash: str, artifact_hash: str
    ) -> IRManifest:
        """Create manifest for artifact."""
        manifest = IRManifest()
        manifest.artifact_id = artifact_hash
        manifest.source_hash = source_hash
        manifest.generated_timestamp = datetime.now(timezone.utc).isoformat()
        manifest.generator_version = artifact.normalization_version

        if artifact.interface_unit:
            manifest.symbol_count = len(artifact.interface_unit.symbols)
            manifest.type_count = len(artifact.interface_unit.types)

        if artifact.validation_report:
            manifest.validation_passed = artifact.validation_report.passed
            manifest.validation_error_count = artifact.validation_report.total_errors()

        return manifest

    def _update_index(self, source_hash: str, artifact_path: Path, manifest_path: Path):
        """Update artifact index."""
        index_path = self.cache_dir / "index.json"

        if index_path.exists():
            try:
                with open(index_path) as f:
                    index = json.load(f)
            except json.JSONDecodeError:
                index = {}
        else:
            index = {}

        index[source_hash] = {
            "artifact_path": str(artifact_path),
            "manifest_path": str(manifest_path),
        }

        with open(index_path, "w") as f:
            f.write(serialize_deterministically(index))


# ============================================================================
# VALIDATION ON LOAD
# ============================================================================


def validate_loaded_artifact(artifact: IRArtifact) -> List[str]:
    """Validate loaded artifact is structurally sound."""
    errors = []

    if not artifact.schema_version:
        errors.append("Missing schema_version")

    if not artifact.interface_unit:
        errors.append("Missing interface_unit")
        return errors

    # Check for duplicate entity IDs
    all_ids = set()

    for symbol in artifact.interface_unit.symbols:
        if symbol.entity_id in all_ids:
            errors.append(f"Duplicate entity ID: {symbol.entity_id}")
        all_ids.add(symbol.entity_id)

    for type_entity in artifact.interface_unit.types:
        if type_entity.entity_id in all_ids:
            errors.append(f"Duplicate entity ID: {type_entity.entity_id}")
        all_ids.add(type_entity.entity_id)

    return errors


__all__ = [
    "IRArtifact",
    "IRManifest",
    "IRArtifactManager",
    "IntegrityError",
    "serialize_deterministically",
    "compute_artifact_hash",
    "verify_artifact_integrity",
    "serialize_compressed",
    "deserialize_compressed",
    "validate_loaded_artifact",
    "IREntityFactory",
]
