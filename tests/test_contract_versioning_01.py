""" Tests for Contract Versioning - Prompt 1/20 Version Identity Model & Fingerprinting

Testing Level: EASY (50 tests) """

import json
import pytest
from datetime import datetime

from modules.module_06_contract_schema.contract_versioning import (
    ContractVersionMetadata,
    SemanticVersion,
    ContractFingerprintComputer,
    VersionIdentityManager,
)


# ============================================================================
# TEST CONTRACT VERSION METADATA
# ============================================================================
class TestContractVersionMetadata:
    """Test ContractVersionMetadata dataclass."""

    def test_valid_metadata_creation(self):
        """Test creating valid version metadata."""
        metadata = ContractVersionMetadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            contract_fingerprint="a" * 64,
            ir_fingerprint="b" * 64,
            generation_timestamp="2025-01-20T12:00:00Z",
        )

        assert metadata.schema_version == "1.0.0"
        assert metadata.synthesis_version == "1.0.0"
        assert metadata.contract_version == "1.0.0"

    def test_invalid_schema_version_format(self):
        """Test invalid schema version format raises error."""
        with pytest.raises(ValueError, match="schema_version"):
            ContractVersionMetadata(
                schema_version="1.0",  # Invalid: missing patch
                synthesis_version="1.0.0",
                contract_version="1.0.0",
                contract_fingerprint="a" * 64,
                ir_fingerprint="b" * 64,
                generation_timestamp="2025-01-20T12:00:00Z",
            )

    def test_invalid_synthesis_version_format(self):
        """Test invalid synthesis version format raises error."""
        with pytest.raises(ValueError, match="synthesis_version"):
            ContractVersionMetadata(
                schema_version="1.0.0",
                synthesis_version="v1.0.0",  # Invalid: has 'v' prefix
                contract_version="1.0.0",
                contract_fingerprint="a" * 64,
                ir_fingerprint="b" * 64,
                generation_timestamp="2025-01-20T12:00:00Z",
            )

    def test_invalid_contract_fingerprint_length(self):
        """Test invalid fingerprint length raises error."""
        with pytest.raises(ValueError, match="contract_fingerprint"):
            ContractVersionMetadata(
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                contract_version="1.0.0",
                contract_fingerprint="abc123",  # Too short
                ir_fingerprint="b" * 64,
                generation_timestamp="2025-01-20T12:00:00Z",
            )

    def test_invalid_ir_fingerprint_format(self):
        """Test invalid IR fingerprint format raises error."""
        with pytest.raises(ValueError, match="ir_fingerprint"):
            ContractVersionMetadata(
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                contract_version="1.0.0",
                contract_fingerprint="a" * 64,
                ir_fingerprint="ZZZZZZ" + "a" * 58,  # Invalid hex chars
                generation_timestamp="2025-01-20T12:00:00Z",
            )

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        metadata = ContractVersionMetadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            contract_fingerprint="a" * 64,
            ir_fingerprint="b" * 64,
            generation_timestamp="2025-01-20T12:00:00Z",
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert data["schema_version"] == "1.0.0"
        assert "contract_fingerprint" in data

    def test_from_dict_creation(self):
        """Test creation from dictionary."""
        data = {
            "schema_version": "1.0.0",
            "synthesis_version": "1.0.0",
            "contract_version": "1.0.0",
            "contract_fingerprint": "a" * 64,
            "ir_fingerprint": "b" * 64,
            "generation_timestamp": "2025-01-20T12:00:00Z",
            "generator_tool_version": "test-1.0.0",
        }

        metadata = ContractVersionMetadata.from_dict(data)

        assert metadata.schema_version == "1.0.0"
        assert metadata.generator_tool_version == "test-1.0.0"


# ============================================================================
# TEST SEMANTIC VERSION
# ============================================================================
class TestSemanticVersion:
    """Test SemanticVersion parser and comparator."""

    def test_parse_valid_version(self):
        """Test parsing valid semantic version."""
        version = SemanticVersion("1.2.3")

        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert str(version) == "1.2.3"

    def test_parse_invalid_version(self):
        """Test parsing invalid version raises error."""
        with pytest.raises(ValueError):
            SemanticVersion("1.2")  # Missing patch

    def test_version_equality(self):
        """Test version equality comparison."""
        v1 = SemanticVersion("1.2.3")
        v2 = SemanticVersion("1.2.3")
        v3 = SemanticVersion("1.2.4")

        assert v1 == v2
        assert v1 != v3

    def test_version_less_than(self):
        """Test version less than comparison."""
        v1 = SemanticVersion("1.2.3")
        v2 = SemanticVersion("1.2.4")
        v3 = SemanticVersion("1.3.0")
        v4 = SemanticVersion("2.0.0")

        assert v1 < v2
        assert v1 < v3
        assert v1 < v4
        assert v2 < v3
        assert v3 < v4

    def test_version_greater_than(self):
        """Test version greater than comparison."""
        v1 = SemanticVersion("2.0.0")
        v2 = SemanticVersion("1.9.9")

        assert v1 > v2
        assert not (v2 > v1)

    def test_version_less_than_or_equal(self):
        """Test version <= comparison."""
        v1 = SemanticVersion("1.2.3")
        v2 = SemanticVersion("1.2.3")
        v3 = SemanticVersion("1.2.4")

        assert v1 <= v2
        assert v1 <= v3

    def test_version_greater_than_or_equal(self):
        """Test version >= comparison."""
        v1 = SemanticVersion("1.2.4")
        v2 = SemanticVersion("1.2.3")
        v3 = SemanticVersion("1.2.4")

        assert v1 >= v2
        assert v1 >= v3

    def test_is_major_bump(self):
        """Test major version bump detection."""
        v1 = SemanticVersion("1.0.0")
        v2 = SemanticVersion("2.0.0")
        v3 = SemanticVersion("1.1.0")

        assert v2.is_major_bump(v1)
        assert not v3.is_major_bump(v1)

    def test_is_minor_bump(self):
        """Test minor version bump detection."""
        v1 = SemanticVersion("1.0.0")
        v2 = SemanticVersion("1.1.0")
        v3 = SemanticVersion("1.0.1")

        assert v2.is_minor_bump(v1)
        assert not v3.is_minor_bump(v1)

    def test_is_patch_bump(self):
        """Test patch version bump detection."""
        v1 = SemanticVersion("1.0.0")
        v2 = SemanticVersion("1.0.1")
        v3 = SemanticVersion("1.1.0")

        assert v2.is_patch_bump(v1)
        assert not v3.is_patch_bump(v1)


# ============================================================================
# TEST FINGERPRINT COMPUTER
# ============================================================================
class TestContractFingerprintComputer:
    """Test ContractFingerprintComputer."""

    @pytest.fixture
    def computer(self):
        return ContractFingerprintComputer()

    @pytest.fixture
    def sample_clauses(self):
        return [
            {
                "clause_id": "clause_1",
                "clause_type": "layout",
                "subject_reference": {"entity_id": "struct_Point"},
                "constraint_parameters": [
                    {"name": "size_bytes", "value": 8},
                    {"name": "alignment", "value": 4},
                ],
            },
            {
                "clause_id": "clause_2",
                "clause_type": "nullability",
                "subject_reference": {"entity_id": "function_get_data"},
                "constraint_parameters": [{"name": "nullable", "value": False}],
            },
        ]

    def test_compute_fingerprint_deterministic(self, computer, sample_clauses):
        """Test fingerprint computation is deterministic."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex digest

    def test_fingerprint_changes_with_ir(self, computer, sample_clauses):
        """Test fingerprint changes when IR changes."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="b" * 64,  # Different IR
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        assert fp1 != fp2

    def test_fingerprint_changes_with_schema_version(self, computer, sample_clauses):
        """Test fingerprint changes when schema version changes."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.1.0",  # Different schema
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        assert fp1 != fp2

    def test_fingerprint_changes_with_synthesis_version(self, computer, sample_clauses):
        """Test fingerprint changes when synthesis version changes."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.1.0",  # Different synthesis
            clauses=sample_clauses,
        )

        assert fp1 != fp2

    def test_fingerprint_changes_with_clause_content(self, computer, sample_clauses):
        """Test fingerprint changes when clause content changes."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        modified_clauses = [
            {
                "clause_id": "clause_1",
                "clause_type": "layout",
                "subject_reference": {"entity_id": "struct_Point"},
                "constraint_parameters": [
                    {"name": "size_bytes", "value": 16},  # Changed size
                    {"name": "alignment", "value": 4},
                ],
            },
            sample_clauses[1],
        ]

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=modified_clauses,
        )

        assert fp1 != fp2

    def test_fingerprint_invariant_to_clause_order(self, computer, sample_clauses):
        """Test fingerprint doesn't change with clause reordering."""
        fp1 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=sample_clauses,
        )

        # Reverse clause order
        reversed_clauses = list(reversed(sample_clauses))

        fp2 = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=reversed_clauses,
        )

        # Should be identical due to canonicalization
        assert fp1 == fp2

    def test_invalid_ir_fingerprint(self, computer, sample_clauses):
        """Test invalid IR fingerprint raises error."""
        with pytest.raises(ValueError, match="Invalid fingerprint"):
            computer.compute_fingerprint(
                ir_fingerprint="invalid",
                schema_version="1.0.0",
                synthesis_version="1.0.0",
                clauses=sample_clauses,
            )

    def test_invalid_version_format(self, computer, sample_clauses):
        """Test invalid version format raises error."""
        with pytest.raises(ValueError, match="Invalid version"):
            computer.compute_fingerprint(
                ir_fingerprint="a" * 64,
                schema_version="1.0",  # Invalid
                synthesis_version="1.0.0",
                clauses=sample_clauses,
            )


# ============================================================================
# TEST VERSION IDENTITY MANAGER
# ============================================================================
class TestVersionIdentityManager:
    """Test VersionIdentityManager."""

    @pytest.fixture
    def manager(self):
        return VersionIdentityManager()

    @pytest.fixture
    def sample_clauses(self):
        return [
            {
                "clause_id": "test_clause",
                "clause_type": "layout",
                "subject_reference": {"entity_id": "struct_Test"},
            }
        ]

    def test_create_version_metadata(self, manager, sample_clauses):
        """Test creating version metadata."""
        metadata = manager.create_version_metadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            ir_fingerprint="a" * 64,
            clauses=sample_clauses,
        )

        assert isinstance(metadata, ContractVersionMetadata)
        assert metadata.schema_version == "1.0.0"
        assert len(metadata.contract_fingerprint) == 64
        assert metadata.generation_timestamp.endswith("Z")

    def test_verify_fingerprint_valid(self, manager, sample_clauses):
        """Test fingerprint verification succeeds for valid contract."""
        metadata = manager.create_version_metadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            ir_fingerprint="a" * 64,
            clauses=sample_clauses,
        )

        is_valid = manager.verify_fingerprint(metadata, sample_clauses)

        assert is_valid is True

    def test_verify_fingerprint_invalid(self, manager, sample_clauses):
        """Test fingerprint verification fails for modified contract."""
        metadata = manager.create_version_metadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            ir_fingerprint="a" * 64,
            clauses=sample_clauses,
        )

        # Modify clauses
        modified_clauses = [{"clause_id": "modified_clause"}]

        is_valid = manager.verify_fingerprint(metadata, modified_clauses)

        assert is_valid is False

    def test_compare_versions_less_than(self, manager):
        """Test version comparison: less than."""
        result = manager.compare_versions("1.0.0", "1.0.1")
        assert result == -1

    def test_compare_versions_equal(self, manager):
        """Test version comparison: equal."""
        result = manager.compare_versions("1.0.0", "1.0.0")
        assert result == 0

    def test_compare_versions_greater_than(self, manager):
        """Test version comparison: greater than."""
        result = manager.compare_versions("1.1.0", "1.0.0")
        assert result == 1


# ============================================================================
# EDGE CASES & INTEGRATION TESTS
# ============================================================================
class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_zero_version_numbers(self):
        """Test version with zero components."""
        version = SemanticVersion("0.0.1")
        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 1

    def test_large_version_numbers(self):
        """Test version with large numbers."""
        version = SemanticVersion("999.888.777")
        assert version.major == 999

    def test_empty_clause_list_fingerprint(self):
        """Test fingerprint with empty clause list."""
        computer = ContractFingerprintComputer()

        fp = computer.compute_fingerprint(
            ir_fingerprint="a" * 64,
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            clauses=[],
        )

        assert len(fp) == 64

    def test_metadata_roundtrip_serialization(self):
        """Test metadata serialization roundtrip."""
        original = ContractVersionMetadata(
            schema_version="1.0.0",
            synthesis_version="1.0.0",
            contract_version="1.0.0",
            contract_fingerprint="a" * 64,
            ir_fingerprint="b" * 64,
            generation_timestamp="2025-01-20T12:00:00Z",
        )

        # Serialize to dict
        data = original.to_dict()

        # Deserialize back
        restored = ContractVersionMetadata.from_dict(data)

        assert restored.schema_version == original.schema_version
        assert restored.contract_fingerprint == original.contract_fingerprint


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
