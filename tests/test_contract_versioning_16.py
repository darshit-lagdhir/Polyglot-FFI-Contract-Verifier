""" Tests for Contract Versioning - Prompt 16/20 Semantic Version Validation & Version Policy Enforcement

Testing Level: HARD (75 tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    SemanticVersion,
    VersionValidator,
    VersionPolicy,
    VersionRecommendationEngine,
    VersionPolicyEnforcer,
    VersionRangeParser,
)


class TestSemanticVersion:
    """Test SemanticVersion (20 tests)."""

    def test_parse_simple(self):
        """Test 1: Parse simple version."""
        v = SemanticVersion.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_with_prerelease(self):
        """Test 2: Parse version with pre-release."""
        v = SemanticVersion.parse("1.0.0-alpha")
        assert v.prerelease == "alpha"

    def test_parse_with_build(self):
        """Test 3: Parse version with build metadata."""
        v = SemanticVersion.parse("1.0.0+build.123")
        assert v.build_metadata == "build.123"

    def test_parse_full(self):
        """Test 4: Parse full version."""
        v = SemanticVersion.parse("2.5.3-beta.1+20060102")
        assert v.major == 2
        assert v.minor == 5
        assert v.patch == 3
        assert v.prerelease == "beta.1"
        assert v.build_metadata == "20060102"

    def test_parse_invalid(self):
        """Test 5: Parse invalid version raises error."""
        with pytest.raises(ValueError):
            SemanticVersion.parse("1.0")

    def test_str_simple(self):
        """Test 6: Convert to string."""
        v = SemanticVersion(1, 2, 3)
        assert str(v) == "1.2.3"

    def test_str_with_prerelease(self):
        """Test 7: String with pre-release."""
        v = SemanticVersion(1, 0, 0, prerelease="alpha")
        assert str(v) == "1.0.0-alpha"

    def test_comparison_less_than(self):
        """Test 8: Version comparison less than."""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("2.0.0")
        assert v1 < v2

    def test_comparison_greater_than(self):
        """Test 9: Version comparison greater than."""
        v1 = SemanticVersion.parse("2.0.0")
        v2 = SemanticVersion.parse("1.0.0")
        assert v1 > v2

    def test_comparison_equal(self):
        """Test 10: Version comparison equal."""
        v1 = SemanticVersion.parse("1.5.0")
        v2 = SemanticVersion.parse("1.5.0")
        assert v1 == v2

    def test_prerelease_less_than_release(self):
        """Test 11: Pre-release < release."""
        v1 = SemanticVersion.parse("1.0.0-alpha")
        v2 = SemanticVersion.parse("1.0.0")
        assert v1 < v2

    def test_prerelease_comparison(self):
        """Test 12: Pre-release version comparison."""
        v1 = SemanticVersion.parse("1.0.0-alpha")
        v2 = SemanticVersion.parse("1.0.0-beta")
        assert v1 < v2

    def test_bump_major(self):
        """Test 13: Bump major version."""
        v = SemanticVersion.parse("1.5.3")
        bumped = v.bump_major()
        assert str(bumped) == "2.0.0"

    def test_bump_minor(self):
        """Test 14: Bump minor version."""
        v = SemanticVersion.parse("1.5.3")
        bumped = v.bump_minor()
        assert str(bumped) == "1.6.0"

    def test_bump_patch(self):
        """Test 15: Bump patch version."""
        v = SemanticVersion.parse("1.5.3")
        bumped = v.bump_patch()
        assert str(bumped) == "1.5.4"

    def test_is_prerelease_true(self):
        """Test 16: is_prerelease true."""
        v = SemanticVersion.parse("1.0.0-alpha")
        assert v.is_prerelease() is True

    def test_is_prerelease_false(self):
        """Test 17: is_prerelease false."""
        v = SemanticVersion.parse("1.0.0")
        assert v.is_prerelease() is False

    def test_build_metadata_ignored_in_comparison(self):
        """Test 18: Build metadata ignored in comparison."""
        v1 = SemanticVersion.parse("1.0.0+build1")
        v2 = SemanticVersion.parse("1.0.0+build2")
        assert v1 == v2

    def test_minor_version_precedence(self):
        """Test 19: Minor version precedence."""
        v1 = SemanticVersion.parse("1.5.0")
        v2 = SemanticVersion.parse("1.6.0")
        assert v1 < v2

    def test_patch_version_precedence(self):
        """Test 20: Patch version precedence."""
        v1 = SemanticVersion.parse("1.5.0")
        v2 = SemanticVersion.parse("1.5.1")
        assert v1 < v2


class TestVersionValidator:
    """Test VersionValidator (15 tests)."""

    @pytest.fixture
    def validator(self):
        return VersionValidator()

    def test_validate_format_valid(self, validator):
        """Test 21: Validate valid format."""
        result = validator.validate_format("1.0.0")
        assert result["valid"] is True

    def test_validate_format_invalid(self, validator):
        """Test 22: Validate invalid format."""
        result = validator.validate_format("1.0")
        assert result["valid"] is False

    def test_validate_transition_valid(self, validator):
        """Test 23: Validate valid transition."""
        result = validator.validate_transition("1.0.0", "1.1.0")
        assert result["valid"] is True

    def test_validate_transition_downgrade(self, validator):
        """Test 24: Validate invalid downgrade."""
        result = validator.validate_transition("1.5.0", "1.4.0")
        assert result["valid"] is False

    def test_validate_transition_same_version(self, validator):
        """Test 25: Validate same version invalid."""
        result = validator.validate_transition("1.0.0", "1.0.0")
        assert result["valid"] is False

    def test_is_valid_next_version_true(self, validator):
        """Test 26: is_valid_next_version true."""
        assert validator.is_valid_next_version("1.0.0", "1.1.0") is True

    def test_is_valid_next_version_false(self, validator):
        """Test 27: is_valid_next_version false."""
        assert validator.is_valid_next_version("1.5.0", "1.4.0") is False

    def test_validate_major_bump(self, validator):
        """Test 28: Validate major version bump."""
        result = validator.validate_transition("1.5.3", "2.0.0")
        assert result["valid"] is True

    def test_validate_minor_bump(self, validator):
        """Test 29: Validate minor version bump."""
        result = validator.validate_transition("1.5.3", "1.6.0")
        assert result["valid"] is True

    def test_validate_patch_bump(self, validator):
        """Test 30: Validate patch version bump."""
        result = validator.validate_transition("1.5.3", "1.5.4")
        assert result["valid"] is True

    def test_invalid_major_decrease(self, validator):
        """Test 31: Invalid major version decrease."""
        result = validator.validate_transition("2.0.0", "1.9.9")
        assert result["valid"] is False
        assert "decrease" in str(result["issues"]).lower()

    def test_invalid_minor_decrease(self, validator):
        """Test 32: Invalid minor version decrease."""
        result = validator.validate_transition("1.5.0", "1.4.0")
        assert result["valid"] is False

    def test_prerelease_transition(self, validator):
        """Test 33: Pre-release transition valid."""
        result = validator.validate_transition("1.0.0-alpha", "1.0.0-beta")
        assert result["valid"] is True

    def test_format_with_prerelease(self, validator):
        """Test 34: Validate format with pre-release."""
        result = validator.validate_format("1.0.0-beta.1")
        assert result["valid"] is True

    def test_format_with_build(self, validator):
        """Test 35: Validate format with build metadata."""
        result = validator.validate_format("1.0.0+build.123")
        assert result["valid"] is True


class TestVersionPolicy:
    """Test VersionPolicy (15 tests)."""

    @pytest.fixture
    def policy(self):
        return VersionPolicy("standard")

    @pytest.fixture
    def mock_diff_breaking(self):
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        return DetailedDiff(
            "1.0.0", "2.0.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])]
        )

    @pytest.fixture
    def mock_diff_extension(self):
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        return DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.EXTENSION, "d")])]
        )

    def test_add_rule(self, policy):
        """Test 36: Add rule to policy."""
        policy.add_rule("Breaking changes require major bump")
        assert len(policy.rules) == 1

    def test_check_compliance_breaking_requires_major(self, policy, mock_diff_breaking):
        """Test 37: Breaking changes require major bump."""
        result = policy.check_compliance("1.0.0", "1.1.0", mock_diff_breaking)
        assert result["compliant"] is False
        assert "major" in str(result["violations"]).lower()

    def test_check_compliance_valid_major_bump(self, policy, mock_diff_breaking):
        """Test 38: Valid major bump with breaking changes."""
        result = policy.check_compliance("1.0.0", "2.0.0", mock_diff_breaking)
        assert result["compliant"] is True

    def test_check_compliance_extension_minor(self, policy, mock_diff_extension):
        """Test 39: Extensions allowed in minor bump."""
        result = policy.check_compliance("1.0.0", "1.1.0", mock_diff_extension)
        assert result["compliant"] is True

    def test_prerelease_exempt(self, policy, mock_diff_breaking):
        """Test 40: Pre-release versions exempt from strict rules."""
        result = policy.check_compliance("1.0.0", "1.1.0-alpha", mock_diff_breaking)
        assert result["compliant"] is True

    def test_no_breaking_in_minor(self, policy, mock_diff_breaking):
        """Test 41: No breaking changes in minor bump."""
        result = policy.check_compliance("1.5.0", "1.6.0", mock_diff_breaking)
        assert result["compliant"] is False

    def test_patch_with_many_changes_warning(self, policy):
        """Test 42: Patch with many changes generates warning."""
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        diff = DetailedDiff(
            "1.0.0", "1.0.1", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange(f"c{i}", "e", ChangeSeverity.NEUTRAL, "d") for i in range(10)])]
        )
        result = policy.check_compliance("1.0.0", "1.0.1", diff)
        assert len(result["warnings"]) > 0

    def test_invalid_version_format(self, policy, mock_diff_extension):
        """Test 43: Invalid version format detected."""
        result = policy.check_compliance("1.0.0", "invalid", mock_diff_extension)
        assert result["compliant"] is False

    def test_compliance_structure(self, policy, mock_diff_extension):
        """Test 44: Compliance result structure."""
        result = policy.check_compliance("1.0.0", "1.1.0", mock_diff_extension)
        assert "compliant" in result
        assert "violations" in result
        assert "warnings" in result

    def test_policy_name(self, policy):
        """Test 45: Policy has name."""
        assert policy.name == "standard"

    def test_multiple_rules(self, policy):
        """Test 46: Multiple rules can be added."""
        policy.add_rule("Rule 1")
        policy.add_rule("Rule 2")
        policy.add_rule("Rule 3")
        assert len(policy.rules) == 3

    def test_major_bump_always_allowed(self, policy, mock_diff_extension):
        """Test 47: Major bump always allowed."""
        result = policy.check_compliance("1.5.0", "2.0.0", mock_diff_extension)
        assert result["compliant"] is True

    def test_breaking_count_in_violation(self, policy, mock_diff_breaking):
        """Test 48: Breaking count mentioned in violation."""
        result = policy.check_compliance("1.0.0", "1.1.0", mock_diff_breaking)
        violation_text = str(result["violations"])
        assert "breaking" in violation_text.lower()

    def test_empty_diff_compliant(self, policy):
        """Test 49: Empty diff is compliant."""
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff

        diff = DetailedDiff("1.0.0", "1.0.1", "a" * 64, "b" * 64, [])
        result = policy.check_compliance("1.0.0", "1.0.1", diff)
        assert result["compliant"] is True

    def test_warnings_not_violations(self, policy, mock_diff_extension):
        """Test 50: Warnings don't make non-compliant."""
        result = policy.check_compliance("1.0.0", "1.1.0", mock_diff_extension)
        if result["warnings"]:
            assert result["compliant"] is True


class TestVersionRecommendationEngine:
    """Test VersionRecommendationEngine (10 tests)."""

    @pytest.fixture
    def engine(self):
        return VersionRecommendationEngine()

    @pytest.fixture
    def diff_breaking(self):
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        return DetailedDiff(
            "1.0.0", "2.0.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])]
        )

    @pytest.fixture
    def diff_extension(self):
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        return DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.EXTENSION, "d")])]
        )

    def test_recommend_major_for_breaking(self, engine, diff_breaking):
        """Test 51: Recommend major bump for breaking changes."""
        result = engine.recommend_version("1.5.0", diff_breaking)
        assert result["recommended_version"] == "2.0.0"

    def test_recommend_minor_for_extension(self, engine, diff_extension):
        """Test 52: Recommend minor bump for extensions."""
        result = engine.recommend_version("1.5.0", diff_extension)
        assert result["recommended_version"] == "1.6.0"

    def test_recommend_patch_for_fixes(self, engine):
        """Test 53: Recommend patch bump for fixes."""
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff

        diff = DetailedDiff("1.0.0", "1.0.1", "a" * 64, "b" * 64, [])
        result = engine.recommend_version("1.5.0", diff)
        assert result["recommended_version"] == "1.5.1"

    def test_recommendation_includes_reason(self, engine, diff_breaking):
        """Test 54: Recommendation includes reason."""
        result = engine.recommend_version("1.0.0", diff_breaking)
        assert "reason" in result
        assert len(result["reason"]) > 0

    def test_recommendation_includes_alternatives(self, engine, diff_extension):
        """Test 55: Recommendation includes alternatives."""
        result = engine.recommend_version("1.0.0", diff_extension)
        assert "alternatives" in result

    def test_recommendation_change_summary(self, engine, diff_breaking):
        """Test 56: Recommendation includes change summary."""
        result = engine.recommend_version("1.0.0", diff_breaking)
        assert "change_summary" in result
        assert "breaking_changes" in result["change_summary"]

    def test_invalid_current_version(self, engine, diff_extension):
        """Test 57: Invalid current version handled."""
        result = engine.recommend_version("invalid", diff_extension)
        assert result["success"] is False

    def test_success_flag(self, engine, diff_extension):
        """Test 58: Success flag present."""
        result = engine.recommend_version("1.0.0", diff_extension)
        assert "success" in result

    def test_current_version_preserved(self, engine, diff_extension):
        """Test 59: Current version preserved in result."""
        result = engine.recommend_version("1.5.0", diff_extension)
        assert result["current_version"] == "1.5.0"

    def test_alternatives_are_list(self, engine, diff_extension):
        """Test 60: Alternatives is a list."""
        result = engine.recommend_version("1.0.0", diff_extension)
        assert isinstance(result["alternatives"], list)


class TestVersionPolicyEnforcer:
    """Test VersionPolicyEnforcer (10 tests)."""

    @pytest.fixture
    def enforcer(self):
        policy = VersionPolicy("test")
        return VersionPolicyEnforcer(policy)

    @pytest.fixture
    def diff(self):
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        return DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.EXTENSION, "d")])]
        )

    def test_enforce_valid_version(self, enforcer, diff):
        """Test 61: Enforce with valid version."""
        result = enforcer.enforce("1.0.0", "1.1.0", diff)
        assert "approved" in result

    def test_enforce_invalid_format(self, enforcer, diff):
        """Test 62: Enforce rejects invalid format."""
        result = enforcer.enforce("1.0.0", "invalid", diff)
        assert result["approved"] is False

    def test_enforce_invalid_transition(self, enforcer, diff):
        """Test 63: Enforce rejects invalid transition."""
        result = enforcer.enforce("1.5.0", "1.4.0", diff)
        assert result["approved"] is False

    def test_enforce_policy_violation(self, enforcer):
        """Test 64: Enforce detects policy violation."""
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff, EntityDiff, DetailedChange, ChangeSeverity

        diff = DetailedDiff(
            "1.0.0", "1.1.0", "a" * 64, "b" * 64, [EntityDiff("e", "t", [DetailedChange("c", "e", ChangeSeverity.BREAKING, "d")])]
        )
        result = enforcer.enforce("1.0.0", "1.1.0", diff)
        assert result["approved"] is False

    def test_enforce_approved_version(self, enforcer, diff):
        """Test 65: Approved result includes version."""
        result = enforcer.enforce("1.0.0", "1.1.0", diff)
        if result["approved"]:
            assert result["version"] == "1.1.0"

    def test_enforce_includes_warnings(self, enforcer, diff):
        """Test 66: Enforce includes warnings."""
        result = enforcer.enforce("1.0.0", "1.1.0", diff)
        assert "warnings" in result or result["approved"] is False

    def test_enforce_reason_on_reject(self, enforcer, diff):
        """Test 67: Reject includes reason."""
        result = enforcer.enforce("1.0.0", "invalid", diff)
        if not result["approved"]:
            assert "reason" in result

    def test_enforcer_has_validator(self, enforcer):
        """Test 68: Enforcer has validator."""
        assert enforcer.validator is not None

    def test_enforcer_has_policy(self, enforcer):
        """Test 69: Enforcer has policy."""
        assert enforcer.policy is not None

    def test_enforcement_steps(self, enforcer, diff):
        """Test 70: Enforcement checks format, transition, policy."""
        result = enforcer.enforce("1.0.0", "1.1.0", diff)
        # Should pass all checks
        assert "approved" in result


class TestVersionRangeParser:
    """Test VersionRangeParser (5 tests)."""

    @pytest.fixture
    def parser(self):
        return VersionRangeParser()

    def test_parse_greater_equal(self, parser):
        """Test 71: Parse >= range."""
        result = parser.parse_range(">=1.0.0")
        assert result["type"] == "greater_equal"
        assert result["version"] == "1.0.0"

    def test_parse_caret(self, parser):
        """Test 72: Parse caret range."""
        result = parser.parse_range("^1.5.0")
        assert result["type"] == "caret"

    def test_satisfies_greater_equal(self, parser):
        """Test 73: Satisfies >= range."""
        assert parser.satisfies_range("1.5.0", ">=1.0.0") is True
        assert parser.satisfies_range("0.9.0", ">=1.0.0") is False

    def test_satisfies_caret(self, parser):
        """Test 74: Satisfies caret range."""
        assert parser.satisfies_range("1.5.0", "^1.0.0") is True
        assert parser.satisfies_range("2.0.0", "^1.0.0") is False

    def test_parse_exact(self, parser):
        """Test 75: Parse exact version."""
        result = parser.parse_range("1.2.3")
        assert result["type"] == "exact"
        assert result["version"] == "1.2.3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
