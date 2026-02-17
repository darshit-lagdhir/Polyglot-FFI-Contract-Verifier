""" Tests for Contract Versioning - Prompt 18/20 Version Metadata & Provenance Tracking

Testing Level: HARD (75 tests) """

import pytest
from datetime import datetime, timedelta, timezone
from modules.module_06_contract_schema.contract_versioning import (
    Author,
    BuildInfo,
    Certification,
    VersionMetadata,
    Signature,
    VersionProvenance,
    MetadataManager,
    ProvenanceTracker,
    SignatureManager,
    ComplianceChecker,
    MetadataValidator,
    ProvenanceExporter,
)


class TestAuthor:
    """Test Author (5 tests)."""

    def test_create_author(self):
        """Test 1: Create author."""
        author = Author("John Doe", "john@example.com")
        assert author.name == "John Doe"
        assert author.email == "john@example.com"

    def test_author_with_role(self):
        """Test 2: Author with role."""
        author = Author("Jane", "jane@example.com", role="Lead Developer")
        assert author.role == "Lead Developer"

    def test_author_with_timestamp(self):
        """Test 3: Author with timestamp."""
        ts = datetime.now(timezone.utc).isoformat() + "Z"
        author = Author("John", "john@example.com", timestamp=ts)
        assert author.timestamp == ts

    def test_author_to_dict(self):
        """Test 4: Author to dictionary."""
        author = Author("John", "john@example.com", role="Dev")
        data = author.to_dict()
        assert data["name"] == "John"
        assert data["role"] == "Dev"

    def test_author_optional_fields(self):
        """Test 5: Author optional fields are None."""
        author = Author("John", "john@example.com")
        assert author.timestamp is None
        assert author.role is None


class TestBuildInfo:
    """Test BuildInfo (10 tests)."""

    def test_create_build_info(self):
        """Test 6: Create build info."""
        build = BuildInfo(build_number=123)
        assert build.build_number == 123

    def test_build_info_all_fields(self):
        """Test 7: Build info with all fields."""
        build = BuildInfo(build_number=123, builder="CI/CD", source_commit="abc123", tool_version="1.0.0")
        assert build.builder == "CI/CD"
        assert build.source_commit == "abc123"

    def test_build_info_to_dict(self):
        """Test 8: Build info to dictionary."""
        build = BuildInfo(build_number=123, builder="Jenkins")
        data = build.to_dict()
        assert data["build_number"] == 123
        assert data["builder"] == "Jenkins"

    def test_build_timestamp(self):
        """Test 9: Build timestamp."""
        ts = datetime.now(timezone.utc).isoformat() + "Z"
        build = BuildInfo(build_timestamp=ts)
        assert build.build_timestamp == ts

    def test_source_info(self):
        """Test 10: Source information."""
        build = BuildInfo(source_commit="abc123", source_branch="main", source_repo="https://github.com/org/repo")
        assert build.source_commit == "abc123"
        assert build.source_branch == "main"

    def test_compiler_version(self):
        """Test 11: Compiler version."""
        build = BuildInfo(compiler_version="gcc 11.0")
        assert build.compiler_version == "gcc 11.0"

    def test_build_host(self):
        """Test 12: Build host."""
        build = BuildInfo(build_host="builder-01.example.com")
        assert build.build_host == "builder-01.example.com"

    def test_tool_version(self):
        """Test 13: Tool version."""
        build = BuildInfo(tool_version="contract-tool 3.0.0")
        assert build.tool_version == "contract-tool 3.0.0"

    def test_default_values_none(self):
        """Test 14: Default values are None."""
        build = BuildInfo()
        assert build.build_number is None
        assert build.builder is None

    def test_to_dict_includes_all(self):
        """Test 15: to_dict includes all fields."""
        build = BuildInfo(build_number=1, builder="CI")
        data = build.to_dict()
        assert "build_number" in data
        assert "source_commit" in data


class TestCertification:
    """Test Certification (10 tests)."""

    def test_create_certification(self):
        """Test 16: Create certification."""
        cert = Certification("SOC2")
        assert cert.standard == "SOC2"

    def test_certification_with_level(self):
        """Test 17: Certification with level."""
        cert = Certification("SOC2", level="Type II")
        assert cert.level == "Type II"

    def test_certification_with_dates(self):
        """Test 18: Certification with dates."""
        cert = Certification("HIPAA", issued_date="2026-01-01", expires_date="2027-01-01")
        assert cert.issued_date == "2026-01-01"

    def test_is_expired_false(self):
        """Test 19: Not expired."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
        cert = Certification("SOC2", expires_date=future)
        assert cert.is_expired() is False

    def test_is_expired_true(self):
        """Test 20: Is expired."""
        past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        cert = Certification("SOC2", expires_date=past)
        assert cert.is_expired() is True

    def test_no_expiry_not_expired(self):
        """Test 21: No expiry means not expired."""
        cert = Certification("Standard")
        assert cert.is_expired() is False

    def test_certification_with_issuer(self):
        """Test 22: Certification with issuer."""
        cert = Certification("SOC2", issuer="Audit Firm LLC")
        assert cert.issuer == "Audit Firm LLC"

    def test_certification_with_attestation(self):
        """Test 23: Certification with attestation."""
        cert = Certification("HIPAA", attestation="Compliant")
        assert cert.attestation == "Compliant"

    def test_to_dict(self):
        """Test 24: Certification to dictionary."""
        cert = Certification("SOC2", level="Type II")
        data = cert.to_dict()
        assert data["standard"] == "SOC2"
        assert data["level"] == "Type II"

    def test_all_fields(self):
        """Test 25: All fields populated."""
        cert = Certification("Standard", "Level", "2026-01-01", "2027-01-01", "Issuer", "Attestation")
        assert cert.standard == "Standard"
        assert cert.issuer == "Issuer"


class TestVersionMetadata:
    """Test VersionMetadata (15 tests)."""

    def test_create_metadata(self):
        """Test 26: Create metadata."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        assert meta.version == "1.0.0"

    def test_add_certification(self):
        """Test 27: Add certification."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        cert = Certification("SOC2")
        meta.add_certification(cert)
        assert len(meta.certifications) == 1

    def test_add_dependency(self):
        """Test 28: Add dependency."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.add_dependency("libcore", "2.0.0")
        assert meta.dependencies["libcore"] == "2.0.0"

    def test_add_tag(self):
        """Test 29: Add tag."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.add_tag("stable")
        assert "stable" in meta.tags

    def test_add_tag_no_duplicates(self):
        """Test 30: Tags don't duplicate."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.add_tag("stable")
        meta.add_tag("stable")
        assert len(meta.tags) == 1

    def test_get_active_certifications(self):
        """Test 31: Get active certifications."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")

        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
        past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")

        meta.add_certification(Certification("SOC2", expires_date=future))
        meta.add_certification(Certification("Old", expires_date=past))

        active = meta.get_active_certifications()
        assert len(active) == 1
        assert active[0].standard == "SOC2"

    def test_with_author(self):
        """Test 32: Metadata with author."""
        author = Author("John", "john@example.com")
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", author=author)
        assert meta.author.name == "John"

    def test_with_build_info(self):
        """Test 33: Metadata with build info."""
        build = BuildInfo(build_number=123)
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", build_info=build)
        assert meta.build_info.build_number == 123

    def test_with_license(self):
        """Test 34: Metadata with license."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", license="MIT")
        assert meta.license == "MIT"

    def test_custom_metadata(self):
        """Test 35: Custom metadata fields."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.custom_metadata["custom_field"] = "custom_value"
        assert meta.custom_metadata["custom_field"] == "custom_value"

    def test_to_dict(self):
        """Test 36: Metadata to dictionary."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", license="MIT")
        meta.add_tag("stable")
        data = meta.to_dict()
        assert data["version"] == "1.0.0"
        assert data["license"] == "MIT"

    def test_to_dict_with_author(self):
        """Test 37: to_dict includes author."""
        author = Author("John", "john@example.com")
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", author=author)
        data = meta.to_dict()
        assert data["author"] is not None
        assert data["author"]["name"] == "John"

    def test_multiple_dependencies(self):
        """Test 38: Multiple dependencies."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.add_dependency("lib1", "1.0.0")
        meta.add_dependency("lib2", "2.0.0")
        assert len(meta.dependencies) == 2

    def test_multiple_tags(self):
        """Test 39: Multiple tags."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta.add_tag("stable")
        meta.add_tag("production")
        meta.add_tag("certified")
        assert len(meta.tags) == 3

    def test_empty_defaults(self):
        """Test 40: Empty defaults."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        assert len(meta.certifications) == 0
        assert len(meta.dependencies) == 0
        assert len(meta.tags) == 0


class TestSignature:
    """Test Signature (5 tests)."""

    def test_create_signature(self):
        """Test 41: Create signature."""
        sig = Signature("SHA256", "sig_data", "John", "john@example.com")
        assert sig.algorithm == "SHA256"
        assert sig.signer_name == "John"

    def test_signature_with_key_id(self):
        """Test 42: Signature with key ID."""
        sig = Signature("Ed25519", "sig", "John", "j@e.com", public_key_id="0x12345")
        assert sig.public_key_id == "0x12345"

    def test_signature_with_timestamp(self):
        """Test 43: Signature with timestamp."""
        ts = datetime.now(timezone.utc).isoformat() + "Z"
        sig = Signature("SHA256", "sig", "John", "j@e.com", timestamp=ts)
        assert sig.timestamp == ts

    def test_signature_to_dict(self):
        """Test 44: Signature to dictionary."""
        sig = Signature("SHA256", "sig_data", "John", "john@example.com")
        data = sig.to_dict()
        assert data["algorithm"] == "SHA256"
        assert data["signer"]["name"] == "John"

    def test_to_dict_structure(self):
        """Test 45: to_dict has nested signer."""
        sig = Signature("SHA256", "sig", "John", "j@e.com", public_key_id="key1")
        data = sig.to_dict()
        assert "signer" in data
        assert data["signer"]["public_key_id"] == "key1"


class TestVersionProvenance:
    """Test VersionProvenance (10 tests)."""

    def test_create_provenance(self):
        """Test 46: Create provenance."""
        prov = VersionProvenance("1.0.0", "fingerprint123")
        assert prov.version == "1.0.0"
        assert prov.fingerprint == "fingerprint123"

    def test_provenance_with_parent(self):
        """Test 47: Provenance with parent version."""
        prov = VersionProvenance("1.1.0", "fp", parent_version="1.0.0")
        assert prov.parent_version == "1.0.0"

    def test_add_approval(self):
        """Test 48: Add approval."""
        prov = VersionProvenance("1.0.0", "fp")
        prov.add_approval("Jane Smith")
        assert "Jane Smith" in prov.approval_chain

    def test_add_approval_no_duplicates(self):
        """Test 49: Approvals don't duplicate."""
        prov = VersionProvenance("1.0.0", "fp")
        prov.add_approval("John")
        prov.add_approval("John")
        assert len(prov.approval_chain) == 1

    def test_is_signed_true(self):
        """Test 50: is_signed returns true."""
        sig = Signature("SHA256", "sig", "John", "j@e.com")
        prov = VersionProvenance("1.0.0", "fp", signature=sig)
        assert prov.is_signed() is True

    def test_is_signed_false(self):
        """Test 51: is_signed returns false."""
        prov = VersionProvenance("1.0.0", "fp")
        assert prov.is_signed() is False

    def test_with_metadata(self):
        """Test 52: Provenance with metadata."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        prov = VersionProvenance("1.0.0", "fp", metadata=meta)
        assert prov.metadata is not None

    def test_to_dict(self):
        """Test 53: Provenance to dictionary."""
        prov = VersionProvenance("1.0.0", "fp", parent_version="0.9.0")
        prov.add_approval("Approver")
        data = prov.to_dict()
        assert data["version"] == "1.0.0"
        assert "Approver" in data["approval_chain"]

    def test_created_at_timestamp(self):
        """Test 54: Provenance with created_at."""
        ts = datetime.now(timezone.utc).isoformat() + "Z"
        prov = VersionProvenance("1.0.0", "fp", created_at=ts)
        assert prov.created_at == ts

    def test_multiple_approvals(self):
        """Test 55: Multiple approvals."""
        prov = VersionProvenance("1.0.0", "fp")
        prov.add_approval("Alice")
        prov.add_approval("Bob")
        prov.add_approval("Charlie")
        assert len(prov.approval_chain) == 3


class TestMetadataManager:
    """Test MetadataManager (5 tests)."""

    @pytest.fixture
    def manager(self):
        return MetadataManager()

    def test_add_metadata(self, manager):
        """Test 56: Add metadata."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        manager.add_metadata(meta)
        assert manager.get_metadata("1.0.0") is not None

    def test_get_metadata(self, manager):
        """Test 57: Get metadata."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        manager.add_metadata(meta)
        retrieved = manager.get_metadata("1.0.0")
        assert retrieved.version == "1.0.0"

    def test_update_metadata(self, manager):
        """Test 58: Update metadata."""
        meta = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", license="MIT")
        manager.add_metadata(meta)
        success = manager.update_metadata("1.0.0", {"license": "Apache-2.0"})
        assert success is True
        assert manager.get_metadata("1.0.0").license == "Apache-2.0"

    def test_get_versions_by_tag(self, manager):
        """Test 59: Get versions by tag."""
        meta1 = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z")
        meta1.add_tag("stable")
        meta2 = VersionMetadata("2.0.0", "2026-02-01T00:00:00Z")
        meta2.add_tag("stable")
        meta3 = VersionMetadata("3.0.0", "2026-03-01T00:00:00Z")
        meta3.add_tag("beta")

        manager.add_metadata(meta1)
        manager.add_metadata(meta2)
        manager.add_metadata(meta3)

        stable = manager.get_versions_by_tag("stable")
        assert len(stable) == 2

    def test_get_versions_by_author(self, manager):
        """Test 60: Get versions by author."""
        author1 = Author("John", "john@example.com")
        author2 = Author("Jane", "jane@example.com")

        meta1 = VersionMetadata("1.0.0", "2026-01-01T00:00:00Z", author=author1)
        meta2 = VersionMetadata("2.0.0", "2026-02-01T00:00:00Z", author=author1)
        meta3 = VersionMetadata("3.0.0", "2026-03-01T00:00:00Z", author=author2)

        manager.add_metadata(meta1)
        manager.add_metadata(meta2)
        manager.add_metadata(meta3)

        johns_versions = manager.get_versions_by_author("john@example.com")
        assert len(johns_versions) == 2


class TestProvenanceTracker:
    """Test ProvenanceTracker (10 tests)."""

    @pytest.fixture
    def tracker(self):
        return ProvenanceTracker()

    def test_add_provenance(self, tracker):
        """Test 61: Add provenance."""
        prov = VersionProvenance("1.0.0", "fp")
        tracker.add_provenance(prov)
        assert tracker.get_provenance("1.0.0") is not None

    def test_get_provenance(self, tracker):
        """Test 62: Get provenance."""
        prov = VersionProvenance("1.0.0", "fp")
        tracker.add_provenance(prov)
        retrieved = tracker.get_provenance("1.0.0")
        assert retrieved.version == "1.0.0"

    def test_get_provenance_chain(self, tracker):
        """Test 63: Get provenance chain."""
        prov1 = VersionProvenance("1.0.0", "fp1")
        prov2 = VersionProvenance("1.1.0", "fp2", parent_version="1.0.0")
        prov3 = VersionProvenance("1.2.0", "fp3", parent_version="1.1.0")

        tracker.add_provenance(prov1)
        tracker.add_provenance(prov2)
        tracker.add_provenance(prov3)

        chain = tracker.get_provenance_chain("1.2.0")
        assert len(chain) == 3
        assert chain[0].version == "1.2.0"
        assert chain[2].version == "1.0.0"

    def test_verify_chain_valid(self, tracker):
        """Test 64: Verify valid chain."""
        prov1 = VersionProvenance("1.0.0", "fp1")
        prov2 = VersionProvenance("1.1.0", "fp2", parent_version="1.0.0")

        tracker.add_provenance(prov1)
        tracker.add_provenance(prov2)

        result = tracker.verify_chain("1.1.0")
        assert result["valid"] is True

    def test_verify_chain_no_data(self, tracker):
        """Test 65: Verify chain with no data."""
        result = tracker.verify_chain("1.0.0")
        assert result["valid"] is False

    def test_chain_length(self, tracker):
        """Test 66: Chain length reported."""
        prov1 = VersionProvenance("1.0.0", "fp1")
        prov2 = VersionProvenance("1.1.0", "fp2", parent_version="1.0.0")

        tracker.add_provenance(prov1)
        tracker.add_provenance(prov2)

        result = tracker.verify_chain("1.1.0")
        assert result["chain_length"] == 2

    def test_single_version_chain(self, tracker):
        """Test 67: Single version chain."""
        prov = VersionProvenance("1.0.0", "fp")
        tracker.add_provenance(prov)

        chain = tracker.get_provenance_chain("1.0.0")
        assert len(chain) == 1

    def test_chain_stops_at_missing(self, tracker):
        """Test 68: Chain stops at missing parent."""
        prov1 = VersionProvenance("1.1.0", "fp1", parent_version="1.0.0")
        # Don't add parent version
        tracker.add_provenance(prov1)

        chain = tracker.get_provenance_chain("1.1.0")
        assert len(chain) == 1

    def test_get_provenance_not_found(self, tracker):
        """Test 69: Get non-existent provenance."""
        result = tracker.get_provenance("999.0.0")
        assert result is None

    def test_verify_includes_issues(self, tracker):
        """Test 70: Verify includes issues list."""
        prov = VersionProvenance("1.0.0", "fp")
        tracker.add_provenance(prov)

        result = tracker.verify_chain("1.0.0")
        assert "issues" in result


class TestSignatureManager:
    """Test SignatureManager (5 tests)."""

    @pytest.fixture
    def manager(self):
        return SignatureManager()

    def test_create_signature(self, manager):
        """Test 71: Create signature."""
        sig = manager.create_signature("1.0.0", "fp", "John", "j@e.com")
        assert isinstance(sig, Signature)
        assert sig.signer_name == "John"

    def test_signature_has_data(self, manager):
        """Test 72: Created signature has data."""
        sig = manager.create_signature("1.0.0", "fp", "John", "j@e.com")
        assert sig.signature_data is not None
        assert len(sig.signature_data) > 0

    def test_signature_has_timestamp(self, manager):
        """Test 73: Created signature has timestamp."""
        sig = manager.create_signature("1.0.0", "fp", "John", "j@e.com")
        assert sig.timestamp is not None

    def test_verify_signature_valid(self, manager):
        """Test 74: Verify valid signature."""
        sig = manager.create_signature("1.0.0", "fp", "John", "j@e.com")
        result = manager.verify_signature(sig, "1.0.0", "fp")
        assert result["valid"] is True

    def test_verify_signature_no_data(self, manager):
        """Test 75: Verify signature without data."""
        sig = Signature("SHA256", "", "John", "j@e.com")
        result = manager.verify_signature(sig, "1.0.0", "fp")
        assert result["valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
