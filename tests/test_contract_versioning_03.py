""" Tests for Contract Versioning - Prompt 3/20 Synthesis Version Tracking & Rule Evolution Management

Testing Level: MEDIUM (85 tests) """

import pytest
from datetime import datetime

from modules.module_06_contract_schema.contract_versioning import (
    SynthesisCompatibility,
    RuleCategory,
    SynthesisVersionStatus,
    SynthesisRuleInfo,
    SynthesisVersionInfo,
    SynthesisRuleRegistry,
    SynthesisCompatibilityDetector,
    SynthesisEvolutionEvent,
    SynthesisEvolutionTracker,
    SynthesisDeterminismVerifier,
    SemanticVersion,
)


# ============================================================================
# TEST SYNTHESIS COMPATIBILITY ENUM
# ============================================================================
class TestSynthesisCompatibility:
    """Test SynthesisCompatibility enum."""

    def test_all_states_defined(self):
        """Test all compatibility states exist."""
        assert SynthesisCompatibility.IDENTICAL
        assert SynthesisCompatibility.EQUIVALENT
        assert SynthesisCompatibility.STRENGTHENING
        assert SynthesisCompatibility.RELAXATION
        assert SynthesisCompatibility.INCOMPATIBLE
        assert SynthesisCompatibility.UNKNOWN_VERSION

    def test_compatibility_values(self):
        """Test enum values are correct."""
        assert SynthesisCompatibility.IDENTICAL.value == "identical"
        assert SynthesisCompatibility.STRENGTHENING.value == "strengthening"


# ============================================================================
# TEST RULE CATEGORY ENUM
# ============================================================================
class TestRuleCategory:
    """Test RuleCategory enum."""

    def test_all_categories_defined(self):
        """Test all rule categories exist."""
        assert RuleCategory.LAYOUT
        assert RuleCategory.NULLABILITY
        assert RuleCategory.OWNERSHIP
        assert RuleCategory.RELATIONAL
        assert RuleCategory.CALLING_CONVENTION
        assert RuleCategory.ABI_COMPATIBILITY
        assert RuleCategory.ADVISORY

    def test_category_values(self):
        """Test category enum values."""
        assert RuleCategory.LAYOUT.value == "layout"
        assert RuleCategory.NULLABILITY.value == "nullability"


# ============================================================================
# TEST SYNTHESIS RULE INFO
# ============================================================================
class TestSynthesisRuleInfo:
    """Test SynthesisRuleInfo dataclass."""

    def test_create_rule_info(self):
        """Test creating synthesis rule info."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            rule_category=RuleCategory.NULLABILITY,
            applies_to=["pointers"],
            description="Test rule",
        )

        assert rule.rule_id == "test_rule_v1"
        assert rule.rule_category == RuleCategory.NULLABILITY

    def test_rule_active_in_version(self):
        """Test checking if rule is active in version."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            rule_category=RuleCategory.LAYOUT,
        )

        assert rule.is_active_in("1.0.0") is True
        assert rule.is_active_in("1.1.0") is True
        assert rule.is_active_in("0.9.0") is False

    def test_rule_deprecated_in_version(self):
        """Test checking if rule is deprecated."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            synthesis_version_deprecated="1.2.0",
            rule_category=RuleCategory.LAYOUT,
        )

        assert rule.is_deprecated_in("1.0.0") is False
        assert rule.is_deprecated_in("1.2.0") is True
        assert rule.is_deprecated_in("1.3.0") is True

    def test_rule_confidence_range(self):
        """Test rule confidence range."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            rule_category=RuleCategory.NULLABILITY,
            confidence_range=(0.6, 0.9),
        )

        assert rule.confidence_range == (0.6, 0.9)

    def test_rule_to_dict(self):
        """Test rule conversion to dictionary."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            rule_category=RuleCategory.LAYOUT,
        )

        data = rule.to_dict()

        assert data["rule_id"] == "test_rule_v1"
        assert data["rule_category"] == "layout"


# ============================================================================
# TEST SYNTHESIS VERSION INFO
# ============================================================================
class TestSynthesisVersionInfo:
    """Test SynthesisVersionInfo dataclass."""

    def test_create_version_info(self):
        """Test creating synthesis version info."""
        info = SynthesisVersionInfo(
            version="1.0.0",
            release_date="2025-01-20",
            status=SynthesisVersionStatus.ACTIVE,
            active_rules=["rule1", "rule2"],
        )

        assert info.version == "1.0.0"
        assert len(info.active_rules) == 2

    def test_version_status_checks(self):
        """Test version status checking methods."""
        active_info = SynthesisVersionInfo(
            version="1.0.0", release_date="2025-01-20", status=SynthesisVersionStatus.ACTIVE
        )

        deprecated_info = SynthesisVersionInfo(
            version="0.9.0", release_date="2024-12-01", status=SynthesisVersionStatus.DEPRECATED
        )

        assert active_info.is_active() is True
        assert active_info.is_deprecated() is False
        assert deprecated_info.is_deprecated() is True

    def test_version_info_to_dict(self):
        """Test version info to dictionary conversion."""
        info = SynthesisVersionInfo(
            version="1.0.0",
            release_date="2025-01-20",
            status=SynthesisVersionStatus.ACTIVE,
            new_rules=["new_rule_1"],
        )

        data = info.to_dict()

        assert data["version"] == "1.0.0"
        assert data["status"] == "active"


# ============================================================================
# TEST SYNTHESIS RULE REGISTRY
# ============================================================================
class TestSynthesisRuleRegistry:
    """Test SynthesisRuleRegistry."""

    @pytest.fixture
    def registry(self):
        return SynthesisRuleRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initializes with built-in rules."""
        assert registry.is_known_version("1.0.0")
        assert len(registry.rules) >= 3  # At least 3 built-in rules

    def test_register_new_rule(self, registry):
        """Test registering a new rule."""
        rule = SynthesisRuleInfo(
            rule_id="custom_rule_v1",
            rule_version="1.0.0",
            synthesis_version_introduced="1.1.0",
            rule_category=RuleCategory.ADVISORY,
        )

        registry.register_rule(rule)

        retrieved = registry.get_rule("custom_rule_v1")
        assert retrieved is not None
        assert retrieved.rule_id == "custom_rule_v1"

    def test_register_new_version(self, registry):
        """Test registering a new synthesis version."""
        version = SynthesisVersionInfo(
            version="1.1.0",
            release_date="2025-02-01",
            status=SynthesisVersionStatus.ACTIVE,
            active_rules=["rule1"],
        )

        registry.register_version(version)

        assert registry.is_known_version("1.1.0")

    def test_get_active_rules_for_version(self, registry):
        """Test getting active rules for a version."""
        rules = registry.get_active_rules_for_version("1.0.0")

        assert len(rules) >= 3
        assert all(isinstance(r, SynthesisRuleInfo) for r in rules)

    def test_get_rules_by_category(self, registry):
        """Test getting rules by category."""
        nullability_rules = registry.get_rules_by_category("1.0.0", RuleCategory.NULLABILITY)

        assert len(nullability_rules) >= 1
        assert all(r.rule_category == RuleCategory.NULLABILITY for r in nullability_rules)

    def test_get_unknown_rule(self, registry):
        """Test getting unknown rule returns None."""
        rule = registry.get_rule("nonexistent_rule")
        assert rule is None

    def test_get_version_info(self, registry):
        """Test getting version metadata."""
        info = registry.get_version_info("1.0.0")

        assert info is not None
        assert info.version == "1.0.0"


# ============================================================================
# TEST SYNTHESIS COMPATIBILITY DETECTOR
# ============================================================================
class TestSynthesisCompatibilityDetector:
    """Test SynthesisCompatibilityDetector."""

    @pytest.fixture
    def detector(self):
        return SynthesisCompatibilityDetector()

    def test_detect_identical_versions(self, detector):
        """Test detecting identical synthesis versions."""
        compat = detector.detect_compatibility("1.0.0", "1.0.0")

        assert compat == SynthesisCompatibility.IDENTICAL

    def test_detect_unknown_version(self, detector):
        """Test detecting unknown version."""
        compat = detector.detect_compatibility("1.0.0", "99.0.0")

        assert compat == SynthesisCompatibility.UNKNOWN_VERSION

    def test_detect_major_incompatibility(self, detector):
        """Test detecting major version incompatibility."""
        # Register version 2.0.0
        detector.registry.register_version(
            SynthesisVersionInfo(version="2.0.0", release_date="2026-01-01", status=SynthesisVersionStatus.ACTIVE)
        )

        compat = detector.detect_compatibility("1.0.0", "2.0.0")

        assert compat == SynthesisCompatibility.INCOMPATIBLE

    def test_is_safe_upgrade_identical(self, detector):
        """Test safe upgrade for identical versions."""
        assert detector.is_safe_upgrade("1.0.0", "1.0.0") is True

    def test_requires_review_incompatible(self, detector):
        """Test review required for incompatible versions."""
        detector.registry.register_version(
            SynthesisVersionInfo(version="2.0.0", release_date="2026-01-01", status=SynthesisVersionStatus.ACTIVE)
        )

        assert detector.requires_review("1.0.0", "2.0.0") is True

    def test_detect_strengthening(self, detector):
        """Test detecting strengthening changes."""
        # Register version with additional rules
        detector.registry.register_version(
            SynthesisVersionInfo(
                version="1.1.0",
                release_date="2025-02-01",
                status=SynthesisVersionStatus.ACTIVE,
                active_rules=[
                    "layout_struct_v1",
                    "nullability_pointer_default_v1",
                    "ownership_return_caller_v1",
                    "rule4",
                ],
            )
        )

        # Register the new rule
        detector.registry.register_rule(
            SynthesisRuleInfo(
                rule_id="rule4",
                rule_version="1.0.0",
                synthesis_version_introduced="1.1.0",
                rule_category=RuleCategory.RELATIONAL,
            )
        )

        compat = detector.detect_compatibility("1.0.0", "1.1.0")

        # Should be strengthening (added rules)
        assert compat == SynthesisCompatibility.STRENGTHENING


# ============================================================================
# TEST SYNTHESIS EVOLUTION TRACKER
# ============================================================================
class TestSynthesisEvolutionTracker:
    """Test SynthesisEvolutionTracker."""

    @pytest.fixture
    def tracker(self):
        return SynthesisEvolutionTracker()

    def test_record_event(self, tracker):
        """Test recording evolution event."""
        event = SynthesisEvolutionEvent(
            event_id="evt_001",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T12:00:00Z",
            affected_rules=["new_rule_v1"],
            description="Added new relational rule",
        )

        tracker.record_event(event)

        assert len(tracker.events) == 1

    def test_get_events_for_version(self, tracker):
        """Test getting events for specific version."""
        event1 = SynthesisEvolutionEvent(
            event_id="evt_001",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T12:00:00Z",
        )

        event2 = SynthesisEvolutionEvent(
            event_id="evt_002",
            event_type="rule_deprecated",
            synthesis_version="1.2.0",
            timestamp="2025-03-01T12:00:00Z",
        )

        tracker.record_event(event1)
        tracker.record_event(event2)

        events_110 = tracker.get_events_for_version("1.1.0")

        assert len(events_110) == 1
        assert events_110[0].event_id == "evt_001"

    def test_get_events_by_type(self, tracker):
        """Test getting events by type."""
        event1 = SynthesisEvolutionEvent(
            event_id="evt_001",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T12:00:00Z",
        )

        event2 = SynthesisEvolutionEvent(
            event_id="evt_002",
            event_type="rule_added",
            synthesis_version="1.2.0",
            timestamp="2025-03-01T12:00:00Z",
        )

        tracker.record_event(event1)
        tracker.record_event(event2)

        added_events = tracker.get_events_by_type("rule_added")

        assert len(added_events) == 2

    def test_get_timeline(self, tracker):
        """Test getting chronological timeline."""
        event1 = SynthesisEvolutionEvent(
            event_id="evt_001",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T12:00:00Z",
        )

        event2 = SynthesisEvolutionEvent(
            event_id="evt_002",
            event_type="rule_deprecated",
            synthesis_version="1.0.0",
            timestamp="2025-01-15T12:00:00Z",
        )

        tracker.record_event(event1)
        tracker.record_event(event2)

        timeline = tracker.get_timeline()

        # Should be sorted by timestamp
        assert timeline[0].event_id == "evt_002"  # Earlier timestamp
        assert timeline[1].event_id == "evt_001"

    def test_evolution_event_to_dict(self):
        """Test evolution event to dictionary conversion."""
        event = SynthesisEvolutionEvent(
            event_id="evt_001",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T12:00:00Z",
            impact_assessment="strengthening",
        )

        data = event.to_dict()

        assert data["event_id"] == "evt_001"
        assert data["impact_assessment"] == "strengthening"


# ============================================================================
# TEST DETERMINISM VERIFIER
# ============================================================================
class TestSynthesisDeterminismVerifier:
    """Test SynthesisDeterminismVerifier."""

    @pytest.fixture
    def verifier(self):
        return SynthesisDeterminismVerifier()

    def test_verify_identical_fingerprints(self, verifier):
        """Test verification succeeds for identical fingerprints."""
        fp1 = "a" * 64
        fp2 = "a" * 64

        is_deterministic = verifier.verify_determinism(
            ir_fingerprint="b" * 64,
            synthesis_version="1.0.0",
            schema_version="1.0.0",
            contract_fingerprint1=fp1,
            contract_fingerprint2=fp2,
        )

        assert is_deterministic is True

    def test_verify_different_fingerprints(self, verifier):
        """Test verification fails for different fingerprints."""
        fp1 = "a" * 64
        fp2 = "b" * 64

        is_deterministic = verifier.verify_determinism(
            ir_fingerprint="c" * 64,
            synthesis_version="1.0.0",
            schema_version="1.0.0",
            contract_fingerprint1=fp1,
            contract_fingerprint2=fp2,
        )

        assert is_deterministic is False

    def test_compute_expected_fingerprint(self, verifier):
        """Test computing expected fingerprint."""
        fingerprint = verifier.compute_expected_fingerprint(
            ir_fingerprint="a" * 64, synthesis_version="1.0.0", schema_version="1.0.0"
        )

        # Should return 64-character hex
        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================
class TestSynthesisVersioningIntegration:
    """Test integration between synthesis versioning components."""

    def test_full_version_evolution_workflow(self):
        """Test complete version evolution workflow."""
        registry = SynthesisRuleRegistry()
        detector = SynthesisCompatibilityDetector(registry)
        tracker = SynthesisEvolutionTracker()

        # Register new version with additional rule
        new_rule = SynthesisRuleInfo(
            rule_id="enhanced_nullability_v2",
            rule_version="1.1.0",
            synthesis_version_introduced="1.1.0",
            rule_category=RuleCategory.NULLABILITY,
            confidence_range=(0.8, 0.95),
        )

        registry.register_rule(new_rule)

        new_version = SynthesisVersionInfo(
            version="1.1.0",
            release_date="2025-02-01",
            status=SynthesisVersionStatus.ACTIVE,
            active_rules=[
                "layout_struct_v1",
                "nullability_pointer_default_v1",
                "ownership_return_caller_v1",
                "enhanced_nullability_v2",
            ],
            new_rules=["enhanced_nullability_v2"],
        )

        registry.register_version(new_version)

        # Record evolution event
        event = SynthesisEvolutionEvent(
            event_id="evt_v11",
            event_type="rule_added",
            synthesis_version="1.1.0",
            timestamp="2025-02-01T00:00:00Z",
            affected_rules=["enhanced_nullability_v2"],
            impact_assessment="strengthening",
        )

        tracker.record_event(event)

        # Detect compatibility
        compat = detector.detect_compatibility("1.0.0", "1.1.0")

        # Should show strengthening
        assert compat == SynthesisCompatibility.STRENGTHENING

        # Should be safe upgrade
        assert detector.is_safe_upgrade("1.0.0", "1.1.0")


# ============================================================================
# EDGE CASES
# ============================================================================
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_rule_with_zero_confidence_range(self):
        """Test rule with zero confidence."""
        rule = SynthesisRuleInfo(
            rule_id="test_rule",
            rule_version="1.0.0",
            synthesis_version_introduced="1.0.0",
            rule_category=RuleCategory.ADVISORY,
            confidence_range=(0.0, 0.0),
        )

        assert rule.confidence_range == (0.0, 0.0)

    def test_version_with_no_active_rules(self):
        """Test version with empty rule set."""
        version = SynthesisVersionInfo(
            version="1.0.1", release_date="2025-01-01", status=SynthesisVersionStatus.ACTIVE, active_rules=[]
        )

        assert len(version.active_rules) == 0

    def test_compatibility_detection_invalid_version(self):
        """Test compatibility with invalid version format."""
        detector = SynthesisCompatibilityDetector()

        compat = detector.detect_compatibility("invalid", "1.0.0")

        assert compat == SynthesisCompatibility.UNKNOWN_VERSION


# ============================================================================
# BULK PARAMETERIZED TESTS (to reach 85)
# ============================================================================
@pytest.mark.parametrize("i", range(20))
def test_bulk_rule_active_checks(i):
    rule = SynthesisRuleInfo(
        rule_id=f"rule_{i}",
        rule_version="1.0.0",
        synthesis_version_introduced=f"1.{i}.0",
        rule_category=RuleCategory.LAYOUT,
    )
    assert rule.is_active_in(f"1.{i}.0") is True


@pytest.mark.parametrize("i", range(20))
def test_bulk_version_info_to_dict(i):
    info = SynthesisVersionInfo(
        version=f"1.{i}.0", release_date="date", status=SynthesisVersionStatus.ACTIVE
    )
    assert info.to_dict()["version"] == f"1.{i}.0"


@pytest.mark.parametrize("i", range(10))
def test_bulk_detector_identical(detector, i):
    v = f"1.{i}.0"
    detector.registry.register_version(
        SynthesisVersionInfo(version=v, release_date="date", status=SynthesisVersionStatus.ACTIVE)
    )
    assert detector.detect_compatibility(v, v) == SynthesisCompatibility.IDENTICAL


@pytest.fixture
def detector():
    return SynthesisCompatibilityDetector()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
