# Contract Versioning System - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Common Workflows](#common-workflows)
4. [API Reference](#api-reference)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Installation
```python
from modules.module_06_contract_schema.contract_versioning import (
    IntegratedVersioningSystem,
    Author
)

# Create system
system = IntegratedVersioningSystem()
```

### Release Your First Version
```python
# Define author
author = Author(
    name='John Doe',
    email='john@example.com',
    role='Lead Developer'
)

# Release version 1.0.0
result = system.release_version(
    current_version='1.0.0',
    candidate_contract=my_contract,
    author=author
)

if result['success']:
    print(f"Released {result['proposed_version']}")
```

## Core Concepts

### 1. Version Fingerprinting
Every contract version has a unique fingerprint:

```python
from modules.module_06_contract_schema.contract_versioning import (
    ContractFingerprintComputer
)

# Note: Using Computer class as per implementation
computer = ContractFingerprintComputer()
fingerprint = computer.compute_fingerprint(contract)
print(f"Fingerprint: {fingerprint}")  # SHA-256 hash
```

### 2. Change Detection
Detect changes between versions:

```python
from modules.module_06_contract_schema.contract_versioning import (
    DetailedDiffAnalyzer
)

analyzer = DetailedDiffAnalyzer()
diff = analyzer.analyze(baseline_contract, candidate_contract)

# Get statistics
stats = diff.get_statistics()
print(f"Breaking changes: {stats['by_severity']['breaking']}")
print(f"New features: {stats['by_severity']['extension']}")
```

### 3. Semantic Versioning
Automatic version recommendation:

```python
from modules.module_06_contract_schema.contract_versioning import (
    VersionRecommendationEngine
)

engine = VersionRecommendationEngine()
recommendation = engine.recommend_version('1.5.0', diff)

print(f"Recommended: {recommendation['recommended_version']}")
print(f"Reason: {recommendation['reason']}")
```

### 4. Version Lifecycle
Track version lifecycle:

```python
from modules.module_06_contract_schema.contract_versioning import (
    LifecycleManager,
    LifecycleStage,
    SupportTier
)

manager = LifecycleManager()

# Deprecate version
manager.deprecate_version(
    version='1.0.0',
    reason='Superseded by 2.0.0',
    eol_days=365,
    replacement_version='2.0.0'
)

# Check status
lifecycle = manager.get_lifecycle('1.0.0')
print(f"Status: {lifecycle.get_support_description()}")
```

## Common Workflows

### Workflow 1: Complete Version Release
```python
from modules.module_06_contract_schema.contract_versioning import (
    IntegratedVersioningSystem,
    Author,
    VersionMetadata
)

# Initialize system
system = IntegratedVersioningSystem()

# 1. Prepare release
author = Author('Jane Smith', 'jane@example.com')
preparation = system.release_workflow.prepare_release(
    current_version='1.5.0',
    candidate_contract=new_contract,
    author=author,
    baseline_contract=old_contract
)

if not preparation['success']:
    print(f"Error: {preparation['error']}")
    print(f"Violations: {preparation.get('violations', [])}")
    exit(1)

# 2. Review changelog
if 'changelog' in preparation:
    changelog = preparation['changelog']
    print(f"\n--- CHANGELOG ---")
    print(f"Version: {changelog['to_version']}")
    print(f"Entries: {len(changelog['entries'])}")

# 3. Finalize release
metadata = VersionMetadata(
    version=preparation['proposed_version'],
    created_at=preparation['metadata']['created_at'],
    license='MIT'
)

finalization = system.release_workflow.finalize_release(
    preparation['proposed_version'],
    metadata,
    fingerprint='contract_fingerprint_here'
)

print(f"\n✅ Released {finalization['version']}")
```

### Workflow 2: Safe Version Upgrade
```python
# Plan upgrade
plan = system.upgrade_workflow.plan_upgrade('1.0.0', '2.0.0')

print(f"Upgrade Plan:")
print(f"  Safe to proceed: {plan['safe_to_proceed']}")
print(f"  Checks: {len(plan['checks'])} completed")
print(f"  Warnings: {len(plan['warnings'])}")

# Show warnings
for warning in plan['warnings']:
    print(f"  ⚠️  {warning}")

# Execute if safe
if plan['safe_to_proceed']:
    execution = system.upgrade_workflow.execute_upgrade('1.0.0', '2.0.0')
    print(f"\n✅ Upgrade completed at {execution['completed_at']}")
else:
    print("\n❌ Upgrade not safe - review warnings")
```

### Workflow 3: Emergency Rollback
```python
# Plan rollback
rollback_plan = system.rollback_workflow.plan_rollback('2.0.0', '1.5.0')

print(f"Rollback Analysis:")
print(f"  Recommended: {rollback_plan['recommended']}")

safety = rollback_plan['safety_analysis']
print(f"  Safety: {safety['safety']}")
print(f"  Risks: {len(safety['risks'])}")
print(f"  Data at risk: {safety['data_at_risk']}")

# Execute with force if needed
execution = system.rollback_version(
    from_version='2.0.0',
    to_version='1.5.0',
    force=True  # Override safety checks in emergency
)

if execution['success']:
    print(f"\n✅ Rolled back at {execution['execution']['rolled_back_at']}")
```

### Workflow 4: Dependency Management
```python
from modules.module_06_contract_schema.contract_versioning import (
    DependencyGraph,
    ContractDependency,
    VersionConstraint,
    ConstraintOperator,
    DependencyResolver
)

# Build dependency graph
graph = DependencyGraph()

# Add contracts
libcore = ContractDependency('libcore', '2.0.0')
app = ContractDependency('app', '3.0.0')

# Add dependency constraint
app.add_dependency(VersionConstraint(
    'libcore',
    ConstraintOperator.GREATER_EQUAL,
    '2.0.0'
))

graph.add_contract(libcore)
graph.add_contract(app)

# Resolve dependencies
resolver = DependencyResolver(graph)
resolution = resolver.resolve('app')

if resolution['success']:
    print(f"Dependencies resolved:")
    for name, version in resolution['resolved_dependencies'].items():
        print(f"  {name}: {version}")
else:
    print(f"Conflicts: {resolution['conflicts']}")
```

### Workflow 5: Generate Documentation
```python
from modules.module_06_contract_schema.contract_versioning import (
    ChangelogGenerator,
    ReleaseNotesGenerator,
    MigrationGuideGenerator,
    ChangelogFormat,
    ChangelogFormatter
)

# Generate changelog
changelog_gen = ChangelogGenerator()
changelog = changelog_gen.generate(diff, '1.0.0', '2.0.0')

# Format as Markdown
formatter = ChangelogFormatter()
markdown = formatter.format(changelog, ChangelogFormat.MARKDOWN)

with open('CHANGELOG.md', 'w') as f:
    f.write(markdown)

# Generate release notes
notes_gen = ReleaseNotesGenerator()
release_notes = notes_gen.generate(changelog)

with open('RELEASE_NOTES.md', 'w') as f:
    f.write(release_notes)

# Generate migration guide
migration_gen = MigrationGuideGenerator()
migration_guide = migration_gen.generate(changelog)

with open('MIGRATION_GUIDE.md', 'w') as f:
    f.write(migration_guide)

print("✅ Documentation generated")
```

## API Reference

### IntegratedVersioningSystem
Main entry point for all versioning operations.

**Methods:**
- `release_version(current_version, candidate_contract, author, baseline_contract=None)`
- `upgrade_version(from_version, to_version)`
- `rollback_version(from_version, to_version, force=False)`

### DetailedDiffAnalyzer
Analyzes differences between contract versions.

**Methods:**
- `analyze(baseline_contract, candidate_contract) -> DetailedDiff`

### VersionRecommendationEngine
Recommends next version based on changes.

**Methods:**
- `recommend_version(current_version, diff) -> Dict`

### LifecycleManager
Manages version lifecycle stages.

**Methods:**
- `add_version(lifecycle)`
- `get_lifecycle(version)`
- `deprecate_version(version, reason, eol_days, replacement_version)`
- `retire_version(version)`

### CompatibilityMatrix
Tracks version compatibility.

**Methods:**
- `add_entry(entry)`
- `get_compatibility(contract_a, version_a, contract_b, version_b)`
- `get_compatible_versions(contract_a, version_a, contract_b)`

## Best Practices

### 1. Version Naming
- ✅ **DO**: Use semantic versioning (MAJOR.MINOR.PATCH)
- ✅ **DO**: Increment MAJOR for breaking changes
- ✅ **DO**: Increment MINOR for new features
- ✅ **DO**: Increment PATCH for bug fixes
- ❌ **DON'T**: Skip versions
- ❌ **DON'T**: Use dates as versions (e.g., 2024.01.15)

### 2. Change Management
- ✅ **DO**: Always compute diffs before releasing
- ✅ **DO**: Review breaking changes carefully
- ✅ **DO**: Document all changes in changelog
- ❌ **DON'T**: Release without policy validation
- ❌ **DON'T**: Ignore compatibility warnings

### 3. Deprecation Policy
- ✅ **DO**: Provide minimum 6 months notice
- ✅ **DO**: Specify replacement version
- ✅ **DO**: Include migration guide
- ❌ **DON'T**: Deprecate without replacement
- ❌ **DON'T**: Remove support suddenly

### 4. Dependency Management
- ✅ **DO**: Use version constraints (>=, ^)
- ✅ **DO**: Resolve conflicts before release
- ✅ **DO**: Test with all supported versions
- ❌ **DON'T**: Use exact version requirements (==) unless necessary
- ❌ **DON'T**: Create circular dependencies

### 5. Rollback Safety
- ✅ **DO**: Test rollback in staging first
- ✅ **DO**: Create backups before rollback
- ✅ **DO**: Check rollback safety analysis
- ❌ **DON'T**: Force rollback without understanding risks
- ❌ **DON'T**: Rollback in production without plan

## Troubleshooting

### Error: "Policy violation detected"
**Cause:** Version bump doesn't match change severity
**Solution:**
```python
# Check what version was recommended
recommendation = engine.recommend_version(current_version, diff)
print(f"Use: {recommendation['recommended_version']}")
```

### Error: "Dependency conflict"
**Cause:** Incompatible version constraints
**Solution:**
```python
# Check conflict details
resolver = DependencyResolver(graph)
resolution = resolver.resolve(contract)
print(f"Conflicts: {resolution['conflicts']}")

# Resolve by updating constraints or versions
```

### Error: "Unsafe rollback"
**Cause:** Rollback would cause data loss
**Solution:**
```python
# Review safety analysis
analysis = rollback_analyzer.analyze_rollback(from_v, to_v)
print(f"Risks: {[r.description for r in analysis.risks]}")

# Use force=True only in emergency:
system.rollback_version(from_v, to_v, force=True)
```

## Support
For issues or questions:
1. Check this guide
2. Review test files in `tests/test_contract_versioning_*.py`
3. See module documentation in `CONTRACT_VERSIONING.md`

## License
See project LICENSE file.
