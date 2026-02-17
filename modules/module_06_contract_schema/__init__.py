"""
Module 06: Contract Schema & Synthesis

PFCV Contract Schema system for expressing, validating, and enforcing FFI interface assumptions.

The Contract Schema transforms implicit FFI assumptions into explicit, machine-verifiable contracts. It provides:

- Contract Generation: Automatic contract creation from IR artifacts
- Validation: Multi-layer validation (schema, referential, constraint)
- Versioning: Semantic versioning with compatibility tracking
- Diffing: Advanced contract comparison with migration guidance
- Serialization: JSON persistence with integrity verification
- Enforcement: Runtime constraint checking via language adapters
- CLI: Command-line interface for all operations

Quick Start:
    >>> from module_06_contract_schema import ContractGenerator
    >>>
    >>> # Generate contract from IR
    >>> generator = ContractGenerator()
    >>> contract = generator.generate(ir_artifact, "my_interface")
    >>>
    >>> # Validate contract
    >>> from module_06_contract_schema import ContractValidator
    >>> validator = ContractValidator()
    >>> result = validator.validate(contract)
    >>> print(f"Valid: {result.passed}")

Public API organized by category:

- Core Entities: ContractDocument, ContractHeader, ContractClause, SubjectReference, ConstraintParameter
- Typed Clauses: LayoutClause, SizeClause, AlignmentClause, NullabilityClause, OwnershipClause, LifetimeClause, RelationalClause, CallingConventionClause
- Generation: ContractGenerator, GenerationConfig
- Validation: ContractValidator, ValidationContext, ValidationResult
- Versioning: SemanticVersion, ContractDiff, VersionRecommender
- Serialization: ContractSerializer, ContractDeserializer, ContractFileManager, ContractArtifactManager
- Diffing: AdvancedContractDiffer, AdvancedDiffResult, MigrationGuide, MigrationStep
- Enforcement: EnforcementEngine, LanguageAdapter, PythonAdapter, EnforcementMode, EnforcementViolation
- CLI: cli, main
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

# Version information
from .version import (
    version,
    version_info,
    get_version,
)

# Set version as package attribute
__version__ = version
__version_info__ = version_info

# Core entities (Prompt 1)
from .contract_entities import (
    # Document structure
    ContractDocument,
    ContractHeader,
    ContractClause,
    # References and parameters
    SubjectReference,
    ConstraintParameter,
    # Metadata
    GenerationMetadata,
    # Enumerations
    SchemaVersion,
    GenerationMode,
    ContractSeverity as Severity,
    ClauseType,
    SubjectKind,
)

# Typed clauses (Prompt 2)
from .clause_types import (
    # Base
    TypedClause,
    # Concrete clause types
    LayoutClause,
    SizeClause,
    AlignmentClause,
    NullabilityClause,
    OwnershipClause,
    LifetimeClause,
    RelationalClause,
    CallingConventionClause,
    ABICompatibilityClause,
    # Factory
    create_clause_from_type,
)

# Validation (Prompt 3)
from .contract_validation import (
    # Core validation
    ContractValidator,
    ValidationContext,
    # Results
    ValidationResult,
    CompleteValidationResult,
    ValidationError,
    ValidationWarning,
    # Layer enum
    ValidationLayer,
)

# Versioning (Prompt 1, 2, 3 & 4/20)
from .contract_versioning import (
    # Identity (Prompt 1)
    ContractVersionMetadata,
    ContractFingerprintComputer,
    VersionIdentityManager,
    # Version types
    SemanticVersion,
    # Schema Evolution (Prompt 2)
    SchemaCompatibility,
    SchemaVersionStatus,
    SchemaVersionInfo,
    SchemaEvolutionRegistry,
    SchemaCompatibilityDetector,
    SchemaMigrationPath,
    SchemaMigrationRegistry,
    SchemaUpgradeChecker,
    # Synthesis (Prompt 3)
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
    # Contract Evolution (Prompt 4)
    ABICompatibility,
    ChangeType,
    ContractChange,
    ContractDiff,
    ContractVersionSnapshot,
    ContractEvolutionTimeline,
    ABICompatibilityDetector,
    MigrationNecessity,
    MigrationNecessityAnalyzer,
    ContractVersionComparator,
    # Compatibility Matrix (Prompt 5)
    CompatibilityRelationship,
    VersionConstraint,
    VersionRange,
    CompatibilityMatrixEntry,
    CompatibilityMatrix,
    CompatibilityMatrixBuilder,
    UpgradePath,
    UpgradePathFinder,
    DependencyResolver,
    # Change tracking (Pending re-implementation in later prompts)
    # ChangeType,
    # CompatibilityImpact,
    # ContractChange,
    # History
    # VersionHistory,
    # VersionHistoryEntry,
    # Diffing
    # ContractDiff,
    # ContractDiffer,
    # Recommendations
    # VersionRecommender,
    # Deprecation
    # DeprecationNotice,
)

# Serialization (Prompt 5)
from .contract_serialization import (
    # Integrity
    IntegrityInfo,
    compute_checksum,
    verify_checksum,
    # Serialization
    ContractSerializer,
    ContractDeserializer,
    # File management
    ContractFileManager,
    ContractArtifactManager,
    # Errors
    SerializationError,
    DeserializationError,
    ContractIntegrityError as IntegrityError,
)

# Generation (Prompt 6)
from .contract_generation import (
    # Configuration
    GenerationConfig,
    # Generator
    ContractGenerator,
    # Results
    GeneratedClause,
    # Pattern matching
    NamingPatternMatcher,
)

# Advanced diffing (Prompt 7)
from .contract_diff_advanced import (
    # Change classification
    ChangeCategory,
    ChangeImpact,
    MigrationDifficulty,
    # Detailed changes
    ParameterChange,
    DetailedClauseChange,
    # Migration
    MigrationStep,
    MigrationGuide,
    # Diff result
    AdvancedDiffResult,
    # Differ
    AdvancedContractDiffer,
)

# CLI (Prompt 8)
from .contract_cli import (
    cli,
    main,
)

# Enforcement (Prompt 9)
from .enforcement_boundary import (
    # Modes and types
    EnforcementMode,
    ViolationType,
    # Violations
    EnforcementViolation,
    # Statistics
    EnforcementStats,
    # Adapters
    LanguageAdapter,
    PythonAdapter,
    # Engine
    EnforcementEngine,
)


def load_contract(path: Path) -> ContractDocument:
    """
    Load contract from file.

    Convenience function that handles deserialization and validation.

    Args:
        path: Path to contract JSON file

    Returns:
        Loaded ContractDocument

    Raises:
        DeserializationError: If file cannot be loaded

    Example:
        >>> contract = load_contract(Path("contract.json"))
        >>> print(f"Loaded {len(contract.clauses)} clauses")
    """
    manager = ContractFileManager()
    return manager.load(path)


def save_contract(contract: ContractDocument, path: Path):
    """
    Save contract to file.

    Convenience function that handles serialization.

    Args:
        contract: Contract to save
        path: Target file path

    Raises:
        SerializationError: If file cannot be saved

    Example:
        >>> save_contract(contract, Path("contract.json"))
    """
    manager = ContractFileManager()
    manager.save(contract, path)


def quick_validate(contract: ContractDocument) -> bool:
    """
    Quick validation check (schema only).

    Performs fast schema validation without referential or constraint checks.
    Useful for quick sanity checks.

    Args:
        contract: Contract to validate

    Returns:
        True if schema valid

    Example:
        >>> if quick_validate(contract):
            ...     print("Contract structure is valid")
    """
    validator = ContractValidator()
    result = validator.validate(contract, skip_referential=True, skip_constraint=True)
    return result.schema_result.passed


# Public API Exports
__all__ = [
    # Version
    "version",
    "version_info",
    "get_version",
    # Core entities
    "ContractDocument",
    "ContractHeader",
    "ContractClause",
    "SubjectReference",
    "ConstraintParameter",
    "GenerationMetadata",
    # Enums
    "SchemaVersion",
    "GenerationMode",
    "Severity",
    "ClauseType",
    "SubjectKind",
    # Typed clauses
    "TypedClause",
    "LayoutClause",
    "SizeClause",
    "AlignmentClause",
    "NullabilityClause",
    "OwnershipClause",
    "LifetimeClause",
    "RelationalClause",
    "CallingConventionClause",
    "ABICompatibilityClause",
    "create_clause_from_type",
    # Validation
    "ContractValidator",
    "ValidationContext",
    "ValidationResult",
    "CompleteValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ValidationLayer",
    # Versioning (Prompt 1, 2, 3 & 4)
    "ContractVersionMetadata",
    "ContractFingerprintComputer",
    "VersionIdentityManager",
    "SemanticVersion",
    "SchemaCompatibility",
    "SchemaVersionStatus",
    "SchemaVersionInfo",
    "SchemaEvolutionRegistry",
    "SchemaCompatibilityDetector",
    "SchemaMigrationPath",
    "SchemaMigrationRegistry",
    "SchemaUpgradeChecker",
    "SynthesisCompatibility",
    "RuleCategory",
    "SynthesisVersionStatus",
    "SynthesisRuleInfo",
    "SynthesisVersionInfo",
    "SynthesisRuleRegistry",
    "SynthesisCompatibilityDetector",
    "SynthesisEvolutionEvent",
    "SynthesisEvolutionTracker",
    "SynthesisDeterminismVerifier",
    "ABICompatibility",
    "ChangeType",
    "ContractChange",
    "ContractDiff",
    "ContractVersionSnapshot",
    "ContractEvolutionTimeline",
    "ABICompatibilityDetector",
    "MigrationNecessity",
    "MigrationNecessityAnalyzer",
    "ContractVersionComparator",
    "CompatibilityRelationship",
    "VersionConstraint",
    "VersionRange",
    "CompatibilityMatrixEntry",
    "CompatibilityMatrix",
    "CompatibilityMatrixBuilder",
    "UpgradePath",
    "UpgradePathFinder",
    "DependencyResolver",
    # "ChangeType",
    # "CompatibilityImpact",
    # "ContractChange",
    # "VersionHistory",
    # "ContractDiff",
    # "ContractDiffer",
    # "VersionRecommender",
    # "DeprecationNotice",
    # Serialization
    "IntegrityInfo",
    "compute_checksum",
    "verify_checksum",
    "ContractSerializer",
    "ContractDeserializer",
    "ContractFileManager",
    "ContractArtifactManager",
    "SerializationError",
    "DeserializationError",
    "IntegrityError",
    # Generation
    "GenerationConfig",
    "ContractGenerator",
    "GeneratedClause",
    # Advanced diffing
    "ChangeCategory",
    "ChangeImpact",
    "MigrationDifficulty",
    "ParameterChange",
    "DetailedClauseChange",
    "MigrationStep",
    "MigrationGuide",
    "AdvancedDiffResult",
    "AdvancedContractDiffer",
    # CLI
    "cli",
    "main",
    # Enforcement
    "EnforcementMode",
    "ViolationType",
    "EnforcementViolation",
    "EnforcementStats",
    "LanguageAdapter",
    "PythonAdapter",
    "EnforcementEngine",
    # Utilities
    "load_contract",
    "save_contract",
    "quick_validate",
]

# Module Metadata
__author__ = "PFCV Team"
__email__ = "team@pfcv.dev"
__license__ = "MIT"
__copyright__ = "Copyright 2025 PFCV Team"
