""" Tests for Contract Versioning - Prompt 17/20 Version Changelog Generation & Release Notes Automation

Testing Level: HARD (75 tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    ChangelogFormat,
    ChangelogEntry,
    Changelog,
    ChangelogGenerator,
    ReleaseNotesGenerator,
    MigrationGuideGenerator,
    ChangelogFormatter,
    ChangelogComparer,
)


class TestChangelogEntry:
    """Test ChangelogEntry (10 tests)."""

    def test_create_entry(self):
        """Test 1: Create changelog entry."""
        entry = ChangelogEntry("feature", "Added new function")
        assert entry.category == "feature"
        assert entry.description == "Added new function"

    def test_to_markdown_simple(self):
        """Test 2: Convert simple entry to markdown."""
        entry = ChangelogEntry("feature", "Added functionality")
        md = entry.to_markdown()
        assert "Added functionality" in md

    def test_to_markdown_with_entity(self):
        """Test 3: Markdown with entity ID."""
        entry = ChangelogEntry("feature", "New function", entity_id="process_batch")
        md = entry.to_markdown()
        assert "process_batch" in md

    def test_to_markdown_with_severity(self):
        """Test 4: Markdown with severity badge."""
        entry = ChangelogEntry("breaking", "Removed function", severity="BREAKING")
        md = entry.to_markdown()
        assert "BREAKING" in md

    def test_to_markdown_with_migration_hint(self):
        """Test 5: Markdown with migration hint."""
        entry = ChangelogEntry("breaking", "Changed signature", migration_hint="Update calls")
        md = entry.to_markdown()
        assert "Migration" in md

    def test_to_dict(self):
        """Test 6: Entry to dictionary."""
        entry = ChangelogEntry("feature", "Added feature", entity_id="func")
        data = entry.to_dict()
        assert data["category"] == "feature"
        assert data["entity_id"] == "func"

    def test_with_details(self):
        """Test 7: Entry with details."""
        entry = ChangelogEntry("bugfix", "Fixed leak", details="Memory leak in cleanup")
        assert entry.details == "Memory leak in cleanup"

    def test_optional_fields(self):
        """Test 8: Optional fields are None."""
        entry = ChangelogEntry("internal", "Refactored code")
        assert entry.entity_id is None
        assert entry.migration_hint is None

    def test_all_fields_populated(self):
        """Test 9: All fields populated."""
        entry = ChangelogEntry("breaking", "Change", "entity", "BREAKING", "Migrate", "Details")
        assert entry.category == "breaking"
        assert entry.severity == "BREAKING"

    def test_markdown_multiline(self):
        """Test 10: Markdown with migration creates multiline."""
        entry = ChangelogEntry("breaking", "Desc", migration_hint="Hint")
        md = entry.to_markdown()
        assert "\n" in md


class TestChangelog:
    """Test Changelog (15 tests)."""

    def test_create_changelog(self):
        """Test 11: Create changelog."""
        log = Changelog("1.0.0", "2.0.0")
        assert log.from_version == "1.0.0"
        assert log.to_version == "2.0.0"

    def test_add_entry(self):
        """Test 12: Add entry to changelog."""
        log = Changelog("1.0.0", "2.0.0")
        entry = ChangelogEntry("feature", "Added feature")
        log.add_entry(entry)
        assert len(log.entries) == 1

    def test_get_entries_by_category(self):
        """Test 13: Get entries by category."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("feature", "Feature 1"))
        log.add_entry(ChangelogEntry("bugfix", "Fix 1"))
        log.add_entry(ChangelogEntry("feature", "Feature 2"))

        features = log.get_entries_by_category("feature")
        assert len(features) == 2

    def test_to_markdown_header(self):
        """Test 14: Markdown includes header."""
        log = Changelog("1.0.0", "2.0.0")
        md = log.to_markdown()
        assert "1.0.0" in md
        assert "2.0.0" in md

    def test_to_markdown_with_date(self):
        """Test 15: Markdown with release date."""
        log = Changelog("1.0.0", "2.0.0", release_date="2026-03-01")
        md = log.to_markdown()
        assert "2026-03-01" in md

    def test_to_markdown_with_summary(self):
        """Test 16: Markdown with summary."""
        log = Changelog("1.0.0", "2.0.0", summary="Major release")
        md = log.to_markdown()
        assert "Major release" in md

    def test_to_markdown_categorizes_entries(self):
        """Test 17: Markdown categorizes entries."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("breaking", "Breaking change"))
        log.add_entry(ChangelogEntry("feature", "New feature"))
        md = log.to_markdown()
        assert "Breaking Changes" in md
        assert "New Features" in md

    def test_to_dict(self):
        """Test 18: Changelog to dictionary."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("feature", "Feature"))
        data = log.to_dict()
        assert data["from_version"] == "1.0.0"
        assert len(data["entries"]) == 1

    def test_empty_changelog(self):
        """Test 19: Empty changelog."""
        log = Changelog("1.0.0", "1.0.1")
        assert len(log.entries) == 0

    def test_multiple_categories(self):
        """Test 20: Multiple categories."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("breaking", "BC"))
        log.add_entry(ChangelogEntry("feature", "F"))
        log.add_entry(ChangelogEntry("bugfix", "BF"))

        assert len(log.get_entries_by_category("breaking")) == 1
        assert len(log.get_entries_by_category("feature")) == 1
        assert len(log.get_entries_by_category("bugfix")) == 1

    def test_category_order_in_markdown(self):
        """Test 21: Category order in markdown."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("bugfix", "Fix"))
        log.add_entry(ChangelogEntry("breaking", "Break"))
        md = log.to_markdown()
        # Breaking should come before bugfix
        assert md.index("Breaking") < md.index("Bug Fixes")

    def test_no_date_optional(self):
        """Test 22: Release date is optional."""
        log = Changelog("1.0.0", "2.0.0")
        assert log.release_date is None

    def test_no_summary_optional(self):
        """Test 23: Summary is optional."""
        log = Changelog("1.0.0", "2.0.0")
        assert log.summary is None

    def test_add_multiple_entries(self):
        """Test 24: Add multiple entries."""
        log = Changelog("1.0.0", "2.0.0")
        for i in range(10):
            log.add_entry(ChangelogEntry("feature", f"Feature {i}"))
        assert len(log.entries) == 10

    def test_markdown_empty_categories_omitted(self):
        """Test 25: Empty categories omitted from markdown."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("feature", "Feature"))
        md = log.to_markdown()
        # Should not include Breaking Changes section
        assert "Breaking Changes" not in md


class TestChangelogGenerator:
    """Test ChangelogGenerator (15 tests)."""

    @pytest.fixture
    def generator(self):
        return ChangelogGenerator()

    @pytest.fixture
    def mock_diff(self):
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedDiff,
            EntityDiff,
            DetailedChange,
            ChangeSeverity,
        )

        return DetailedDiff(
            "1.0.0",
            "2.0.0",
            "a" * 64,
            "b" * 64,
            [
                EntityDiff("func1", "function", [DetailedChange("func_added", "func1", ChangeSeverity.EXTENSION, "Added function")]),
                EntityDiff("func2", "function", [DetailedChange("func_removed", "func2", ChangeSeverity.BREAKING, "Removed function")]),
            ],
        )

    def test_generate_changelog(self, generator, mock_diff):
        """Test 26: Generate changelog from diff."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        assert isinstance(log, Changelog)

    def test_generated_versions(self, generator, mock_diff):
        """Test 27: Generated changelog has correct versions."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        assert log.from_version == "1.0.0"
        assert log.to_version == "2.0.0"

    def test_generates_entries(self, generator, mock_diff):
        """Test 28: Generates changelog entries."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        assert len(log.entries) > 0

    def test_generates_summary(self, generator, mock_diff):
        """Test 29: Generates summary."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        assert log.summary is not None

    def test_categorizes_breaking_changes(self, generator, mock_diff):
        """Test 30: Categorizes breaking changes."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        breaking = log.get_entries_by_category("breaking")
        assert len(breaking) > 0

    def test_categorizes_features(self, generator, mock_diff):
        """Test 31: Categorizes features."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        features = log.get_entries_by_category("feature")
        assert len(features) > 0

    def test_migration_hints_for_breaking(self, generator, mock_diff):
        """Test 32: Migration hints for breaking changes."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        breaking = log.get_entries_by_category("breaking")
        # Some breaking changes should have migration hints
        assert any(e.migration_hint for e in breaking)

    def test_entity_ids_preserved(self, generator, mock_diff):
        """Test 33: Entity IDs preserved."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        entity_ids = [e.entity_id for e in log.entries]
        assert "func1" in entity_ids or "func2" in entity_ids

    def test_determine_category_breaking(self, generator):
        """Test 34: Determine category for breaking."""
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedChange,
            ChangeSeverity,
        )

        change = DetailedChange("test", "e", ChangeSeverity.BREAKING, "d")
        category = generator._determine_category(change)
        assert category == "breaking"

    def test_determine_category_extension(self, generator):
        """Test 35: Determine category for extension."""
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedChange,
            ChangeSeverity,
        )

        change = DetailedChange("test", "e", ChangeSeverity.EXTENSION, "d")
        category = generator._determine_category(change)
        assert category == "feature"

    def test_format_description_uses_provided(self, generator):
        """Test 36: Uses provided description."""
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedChange,
            EntityDiff,
            ChangeSeverity,
        )

        change = DetailedChange("test", "e", ChangeSeverity.NEUTRAL, "Custom description")
        entity_diff = EntityDiff("e", "function", [])
        desc = generator._format_description(change, entity_diff)
        assert desc == "Custom description"

    def test_migration_hint_for_removed(self, generator):
        """Test 37: Migration hint for removed items."""
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedChange,
            ChangeSeverity,
        )

        change = DetailedChange("func_removed", "e", ChangeSeverity.BREAKING, "d")
        hint = generator._generate_migration_hint(change)
        assert hint is not None

    def test_no_migration_hint_for_non_breaking(self, generator):
        """Test 38: No migration hint for non-breaking."""
        from modules.module_06_contract_schema.contract_versioning import (
            DetailedChange,
            ChangeSeverity,
        )

        change = DetailedChange("test", "e", ChangeSeverity.EXTENSION, "d")
        hint = generator._generate_migration_hint(change)
        assert hint is None

    def test_empty_diff_generates_empty_log(self, generator):
        """Test 39: Empty diff generates empty changelog."""
        from modules.module_06_contract_schema.contract_versioning import DetailedDiff

        diff = DetailedDiff("1.0.0", "1.0.1", "a" * 64, "b" * 64, [])
        log = generator.generate(diff, "1.0.0", "1.0.1")
        assert len(log.entries) == 0

    def test_summary_reflects_changes(self, generator, mock_diff):
        """Test 40: Summary reflects changes."""
        log = generator.generate(mock_diff, "1.0.0", "2.0.0")
        if log.summary:
            assert "breaking" in log.summary.lower() or "feature" in log.summary.lower()


class TestReleaseNotesGenerator:
    """Test ReleaseNotesGenerator (10 tests)."""

    @pytest.fixture
    def generator(self):
        return ReleaseNotesGenerator()

    @pytest.fixture
    def changelog(self):
        log = Changelog("1.0.0", "2.0.0", release_date="2026-03-01")
        log.add_entry(ChangelogEntry("breaking", "Breaking change", entity_id="func"))
        log.add_entry(ChangelogEntry("feature", "New feature", entity_id="func2"))
        return log

    def test_generate_release_notes(self, generator, changelog):
        """Test 41: Generate release notes."""
        notes = generator.generate(changelog)
        assert isinstance(notes, str)
        assert len(notes) > 0

    def test_includes_version(self, generator, changelog):
        """Test 42: Includes version number."""
        notes = generator.generate(changelog)
        assert "2.0.0" in notes

    def test_includes_date(self, generator, changelog):
        """Test 43: Includes release date."""
        notes = generator.generate(changelog)
        assert "2026-03-01" in notes

    def test_highlights_features(self, generator, changelog):
        """Test 44: Highlights new features."""
        notes = generator.generate(changelog)
        assert "feature" in notes.lower()

    def test_warns_about_breaking(self, generator, changelog):
        """Test 45: Warns about breaking changes."""
        notes = generator.generate(changelog)
        assert "breaking" in notes.lower() or "important" in notes.lower()

    def test_includes_migration_section(self, generator, changelog):
        """Test 46: Includes migration section for breaking."""
        notes = generator.generate(changelog)
        assert "migration" in notes.lower()

    def test_with_template(self, generator, changelog):
        """Test 47: Apply custom template."""
        template = "Version {version} released on {date}"
        notes = generator.generate(changelog, template)
        assert "2.0.0" in notes
        assert "2026-03-01" in notes

    def test_template_replacements(self, generator, changelog):
        """Test 48: Template replacements work."""
        template = "{breaking_count} breaking changes, {feature_count} features"
        notes = generator.generate(changelog, template)
        assert "1 breaking" in notes
        assert "1 feature" in notes

    def test_no_breaking_no_migration_section(self, generator):
        """Test 49: No migration section without breaking changes."""
        log = Changelog("1.0.0", "1.1.0")
        log.add_entry(ChangelogEntry("feature", "Feature"))
        notes = generator.generate(log)
        # Should not emphasize migration
        migration_count = notes.lower().count("migration")
        assert migration_count <= 1  # May appear in footer

    def test_top_features_limited(self, generator):
        """Test 50: Top features limited in highlights."""
        log = Changelog("1.0.0", "2.0.0")
        for i in range(10):
            log.add_entry(ChangelogEntry("feature", f"Feature {i}"))
        notes = generator.generate(log)
        # Should not list all 10 in highlights
        assert notes.count("Feature") < 10


class TestMigrationGuideGenerator:
    """Test MigrationGuideGenerator (10 tests)."""

    @pytest.fixture
    def generator(self):
        return MigrationGuideGenerator()

    @pytest.fixture
    def changelog_with_breaking(self):
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("breaking", "Removed function", "old_func", migration_hint="Use new_func instead"))
        return log

    @pytest.fixture
    def changelog_no_breaking(self):
        log = Changelog("1.0.0", "1.1.0")
        log.add_entry(ChangelogEntry("feature", "Added feature"))
        return log

    def test_generate_migration_guide(self, generator, changelog_with_breaking):
        """Test 51: Generate migration guide."""
        guide = generator.generate(changelog_with_breaking)
        assert isinstance(guide, str)
        assert len(guide) > 0

    def test_includes_version_info(self, generator, changelog_with_breaking):
        """Test 52: Includes version information."""
        guide = generator.generate(changelog_with_breaking)
        assert "1.0.0" in guide
        assert "2.0.0" in guide

    def test_lists_breaking_changes(self, generator, changelog_with_breaking):
        """Test 53: Lists breaking changes."""
        guide = generator.generate(changelog_with_breaking)
        assert "old_func" in guide

    def test_includes_migration_hints(self, generator, changelog_with_breaking):
        """Test 54: Includes migration hints."""
        guide = generator.generate(changelog_with_breaking)
        assert "new_func" in guide

    def test_no_breaking_message(self, generator, changelog_no_breaking):
        """Test 55: Message when no breaking changes."""
        guide = generator.generate(changelog_no_breaking)
        assert "no breaking" in guide.lower()

    def test_numbered_changes(self, generator, changelog_with_breaking):
        """Test 56: Breaking changes are numbered."""
        guide = generator.generate(changelog_with_breaking)
        assert "1." in guide

    def test_multiple_breaking_changes(self, generator):
        """Test 57: Multiple breaking changes."""
        log = Changelog("1.0.0", "2.0.0")
        log.add_entry(ChangelogEntry("breaking", "Change 1", "e1"))
        log.add_entry(ChangelogEntry("breaking", "Change 2", "e2"))
        log.add_entry(ChangelogEntry("breaking", "Change 3", "e3"))
        guide = generator.generate(log)
        assert "1." in guide
        assert "2." in guide
        assert "3." in guide

    def test_migration_steps_section(self, generator, changelog_with_breaking):
        """Test 58: Migration steps section."""
        guide = generator.generate(changelog_with_breaking)
        assert "migration" in guide.lower()

    def test_overview_section(self, generator, changelog_with_breaking):
        """Test 59: Overview section."""
        guide = generator.generate(changelog_with_breaking)
        assert "overview" in guide.lower()

    def test_guide_structure(self, generator, changelog_with_breaking):
        """Test 60: Guide has proper structure."""
        guide = generator.generate(changelog_with_breaking)
        assert "# Migration Guide" in guide
        assert "## Overview" in guide
        assert "## Breaking Changes" in guide


class TestChangelogFormatter:
    """Test ChangelogFormatter (10 tests)."""

    @pytest.fixture
    def formatter(self):
        return ChangelogFormatter()

    @pytest.fixture
    def changelog(self):
        log = Changelog("1.0.0", "2.0.0", release_date="2026-03-01")
        log.add_entry(ChangelogEntry("feature", "New feature"))
        log.add_entry(ChangelogEntry("bugfix", "Fixed bug"))
        return log

    def test_format_markdown(self, formatter, changelog):
        """Test 61: Format as markdown."""
        output = formatter.format(changelog, ChangelogFormat.MARKDOWN)
        assert "#" in output  # Markdown headers

    def test_format_json(self, formatter, changelog):
        """Test 62: Format as JSON."""
        output = formatter.format(changelog, ChangelogFormat.JSON)
        assert "{" in output
        assert '"from_version"' in output

    def test_format_text(self, formatter, changelog):
        """Test 63: Format as plain text."""
        output = formatter.format(changelog, ChangelogFormat.TEXT)
        assert "CHANGELOG" in output

    def test_format_html(self, formatter, changelog):
        """Test 64: Format as HTML."""
        output = formatter.format(changelog, ChangelogFormat.HTML)
        assert "<" in output
        assert "div" in output or "h1" in output

    def test_json_parseable(self, formatter, changelog):
        """Test 65: JSON output is parseable."""
        import json

        output = formatter.format(changelog, ChangelogFormat.JSON)
        data = json.loads(output)
        assert data["from_version"] == "1.0.0"

    def test_text_includes_categories(self, formatter, changelog):
        """Test 66: Text format includes categories."""
        output = formatter.format(changelog, ChangelogFormat.TEXT)
        assert "NEW FEATURES" in output or "BUG FIXES" in output

    def test_html_has_structure(self, formatter, changelog):
        """Test 67: HTML has proper structure."""
        output = formatter.format(changelog, ChangelogFormat.HTML)
        assert "<h1>" in output or "<h2>" in output

    def test_default_format(self, formatter, changelog):
        """Test 68: Default format is markdown."""
        # Pass invalid format, should default to markdown
        output = formatter.format(changelog, "invalid")
        assert "#" in output

    def test_text_separator_lines(self, formatter, changelog):
        """Test 69: Text format has separator lines."""
        output = formatter.format(changelog, ChangelogFormat.TEXT)
        assert "=" in output or "-" in output

    def test_html_css_classes(self, formatter, changelog):
        """Test 70: HTML includes CSS classes."""
        output = formatter.format(changelog, ChangelogFormat.HTML)
        assert "class=" in output


class TestChangelogComparer:
    """Test ChangelogComparer (5 tests)."""

    @pytest.fixture
    def comparer(self):
        return ChangelogComparer()

    @pytest.fixture
    def changelog1(self):
        log = Changelog("1.0.0", "1.1.0")
        log.add_entry(ChangelogEntry("feature", "Feature"))
        return log

    @pytest.fixture
    def changelog2(self):
        log = Changelog("1.1.0", "2.0.0")
        log.add_entry(ChangelogEntry("breaking", "Breaking"))
        log.add_entry(ChangelogEntry("feature", "Feature"))
        return log

    def test_compare_changelogs(self, comparer, changelog1, changelog2):
        """Test 71: Compare two changelogs."""
        result = comparer.compare(changelog1, changelog2)
        assert "changelog1" in result
        assert "changelog2" in result

    def test_compare_entry_counts(self, comparer, changelog1, changelog2):
        """Test 72: Compare entry counts."""
        result = comparer.compare(changelog1, changelog2)
        assert result["changelog1"]["entry_count"] == 1
        assert result["changelog2"]["entry_count"] == 2

    def test_compare_breaking_counts(self, comparer, changelog1, changelog2):
        """Test 73: Compare breaking change counts."""
        result = comparer.compare(changelog1, changelog2)
        assert result["changelog1"]["breaking_count"] == 0
        assert result["changelog2"]["breaking_count"] == 1

    def test_compare_differences(self, comparer, changelog1, changelog2):
        """Test 74: Compare includes differences."""
        result = comparer.compare(changelog1, changelog2)
        assert "differences" in result
        assert "entry_count_diff" in result["differences"]

    def test_difference_calculations(self, comparer, changelog1, changelog2):
        """Test 75: Difference calculations correct."""
        result = comparer.compare(changelog1, changelog2)
        assert result["differences"]["entry_count_diff"] == 1
        assert result["differences"]["breaking_count_diff"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
