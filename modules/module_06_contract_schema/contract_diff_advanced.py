"""
Module 06: Contract Schema - Advanced Diffing and Impact Analysis

This module provides sophisticated change analysis for FFI contracts, including 
semantic classification of changes (Breaking vs. Compatible), migration path 
generation, and detailed impact assessment for developers and automated tooling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from datetime import datetime

from .contract_entities import (
    ContractDocument, ContractClause, ClauseType
)
from .contract_versioning import (
    SemanticVersion, ContractDiff, ContractDiffer, CompatibilityImpact
)

class ChangeCategory(Enum):
    """Specific categories of changes identified during diffing."""
    PARAMETER_VALUE_CHANGED = "parameter_value_changed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    CLAUSE_ADDED = "clause_added"
    CLAUSE_REMOVED = "clause_removed"
    CLAUSE_TYPE_CHANGED = "clause_type_changed"
    METADATA_CHANGED = "metadata_changed"

class ChangeImpact(Enum):
    """Semantic impact of a change on existing FFI bindings."""
    BREAKING = "breaking"        # Requires code changes or recompilation
    COMPATIBLE = "compatible"    # Safe for existing consumers
    NEUTRAL = "neutral"         # No functional or semantic effect
    UNKNOWN = "unknown"          # Impact could not be determined

class MigrationDifficulty(Enum):
    """Estimated effort and complexity of a migration step."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MANUAL = "manual"

@dataclass
class ParameterChange:
        parameter_name: str
    old_value: Any
    new_value: Any
    category: ChangeCategory
    impact: ChangeImpact
    confidence: float = 1.0
    analysis: str = ""

@dataclass
class DetailedClauseChange:
    """In-depth analysis of a change affecting a single contract clause."""
    clause_id: str
    category: ChangeCategory
    impact: ChangeImpact
    old_clause: Optional[ContractClause] = None
    new_clause: Optional[ContractClause] = None
    parameter_changes: List[ParameterChange] = field(default_factory=list)
    confidence: float = 1.0
    description: str = ""
    rationale: str = ""

@dataclass
class MigrationStep:
    """Actionable instructions for resolving a breaking change."""
    change_description: str
    required_action: str
    code_example: Optional[str] = None
    automated: bool = False
    difficulty: MigrationDifficulty = MigrationDifficulty.MANUAL

    def format_step(self) -> str:
        """Produces a human-readable representation of this migration step."""
        lines = [
            f"Change: {self.change_description}",
            f"Action: {self.required_action}"
        ]
        if self.code_example:
            lines.append(f"\nExample:\n{self.code_example}")
        lines.append(f"Automated: {'Yes' if self.automated else 'No'}")
        lines.append(f"Difficulty: {self.difficulty.value.upper()}")
        return "\n".join(lines)

@dataclass
class MigrationGuide:
    """Consolidated migration guidance for a version transition."""
    from_version: SemanticVersion
    to_version: SemanticVersion
    steps: List[MigrationStep] = field(default_factory=list)
    estimated_effort: str = "Unknown"

    def add_step(self, step: MigrationStep):
        self.steps.append(step)

    def format_guide(self) -> str:
        """Produces a complete formatted guide for the entire transition."""
        lines = [
            f"Migration Guide: {self.from_version} -> {self.to_version}",
            "=" * 60,
            f"Effort: {self.estimated_effort}",
            f"Steps: {len(self.steps)}",
            ""
        ]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"\n[Step {i}]")
            lines.append(step.format_step())
        return "\n".join(lines)

@dataclass
class AdvancedDiffResult:
    """Rich diff results including semantic analysis and migration paths."""
    old_version: SemanticVersion
    new_version: SemanticVersion
    detailed_changes: List[DetailedClauseChange] = field(default_factory=list)
    migration_guide: Optional[MigrationGuide] = None
    overall_impact: ChangeImpact = ChangeImpact.NEUTRAL
    confidence: float = 1.0

    def get_breaking_changes(self) -> List[DetailedClauseChange]:
        return [c for c in self.detailed_changes if c.impact == ChangeImpact.BREAKING]

    def has_breaking_changes(self) -> bool:
        return any(c.impact == ChangeImpact.BREAKING for c in self.detailed_changes)

    def format_summary(self) -> str:
        """Produces a human-friendly summary of the contract evolution."""
        breaking = self.get_breaking_changes()
        compatible = [c for c in self.detailed_changes if c.impact == ChangeImpact.COMPATIBLE]
        
        lines = [
            f"Contract Evolution: {self.old_version} -> {self.new_version}",
            "=" * 60,
            f"Overall Impact: {self.overall_impact.value.upper()}",
            ""
        ]
        if breaking:
            lines.append(f"BREAKING CHANGES ({len(breaking)}):")
            for c in breaking[:5]:
                lines.append(f"  ! {c.description}")
            if len(breaking) > 5:
                lines.append(f"  ... and {len(breaking)-5} more.")
            lines.append("")
        
        lines.append(f"Compatible Changes: {len(compatible)}")
        lines.append(f"Neutral Changes:    {len(self.detailed_changes) - len(breaking) - len(compatible)}")
        return "\n".join(lines)

class NullabilityChangeAnalyzer:
        def analyze_impact(self, old_c: ContractClause, new_c: ContractClause) -> ChangeImpact:
        old_val = self._extract_nullable(old_c)
        new_val = self._extract_nullable(new_c)
        
        if old_val is None or new_val is None: return ChangeImpact.UNKNOWN
        if old_val == new_val: return ChangeImpact.NEUTRAL
        
        # Tightening (nullable -> non-nullable) is breaking
        return ChangeImpact.BREAKING if old_val and not new_val else ChangeImpact.COMPATIBLE

    def _extract_nullable(self, clause: ContractClause) -> Optional[bool]:
        p = clause.get_parameter("nullable")
        return p.value if p else None

    def generate_migration_step(self, old_c: ContractClause, new_c: ContractClause) -> Optional[MigrationStep]:
        if self.analyze_impact(old_c, new_c) == ChangeImpact.BREAKING:
            return MigrationStep(
                change_description="Nullability requirement tightened to non-null.",
                required_action="Verify pointer validity before invocation.",
                code_example="if ptr is not None:\n    func(ptr)",
                difficulty=MigrationDifficulty.EASY
            )
        return None

class SizeChangeAnalyzer:
        def analyze_impact(self, old_c: ContractClause, new_c: ContractClause) -> ChangeImpact:
        old_size = self._extract_size(old_c)
        new_size = self._extract_size(new_c)
        
        if old_size is None or new_size is None: return ChangeImpact.UNKNOWN
        if old_size == new_size: return ChangeImpact.NEUTRAL
        
        # Increased size requirement is breaking
        return ChangeImpact.BREAKING if new_size > old_size else ChangeImpact.COMPATIBLE

    def _extract_size(self, clause: ContractClause) -> Optional[int]:
        p = clause.get_parameter("size_value")
        if not p: p = clause.get_parameter("expected_size")
        return p.value if p else None

class OwnershipChangeAnalyzer:
        def analyze_impact(self, old_c: ContractClause, new_c: ContractClause) -> ChangeImpact:
        old_mode = self._extract_mode(old_c)
        new_mode = self._extract_mode(new_c)
        return ChangeImpact.BREAKING if old_mode != new_mode else ChangeImpact.NEUTRAL

    def _extract_mode(self, clause: ContractClause) -> Optional[str]:
        p = clause.get_parameter("ownership_mode")
        return p.value if p else None

class AdvancedContractDiffer:
        
    def __init__(self):
        self.basic_differ = ContractDiffer()
        self.null_analyzer = NullabilityChangeAnalyzer()
        self.size_analyzer = SizeChangeAnalyzer()
        self.own_analyzer = OwnershipChangeAnalyzer()

    def compute_diff(self, old_doc: ContractDocument, new_doc: ContractDocument) -> AdvancedDiffResult:
        basic = self.basic_differ.diff(old_doc, new_doc)
        result = AdvancedDiffResult(basic.old_version, basic.new_version)
        
        old_map = {c.clause_id: c for c in old_doc.clauses}
        new_map = {c.clause_id: c for c in new_doc.clauses}
        
        # Process Additions
        for cid in basic.added_clauses:
            result.detailed_changes.append(DetailedClauseChange(
                cid, ChangeCategory.CLAUSE_ADDED, ChangeImpact.COMPATIBLE,
                new_clause=new_map[cid], description=f"New requirement: {cid}"
            ))

        # Process Removals
        for cid in basic.removed_clauses:
            result.detailed_changes.append(DetailedClauseChange(
                cid, ChangeCategory.CLAUSE_REMOVED, ChangeImpact.BREAKING,
                old_clause=old_map[cid], description=f"Requirement removed: {cid}"
            ))

        # Process Modifications with Semantic Context
        for comp in basic.modified_clauses:
            old_c = old_map[comp.clause_id]
            new_c = new_map[comp.clause_id]
            detailed = self._analyze_clausal_modification(old_c, new_c)
            result.detailed_changes.append(detailed)

        result.overall_impact = ChangeImpact.BREAKING if result.has_breaking_changes() else \
                               (ChangeImpact.COMPATIBLE if basic.added_clauses else ChangeImpact.NEUTRAL)
        
        if result.has_breaking_changes():
            result.migration_guide = self._build_migration_guide(result)
            
        return result

    def _analyze_clausal_modification(self, old_c: ContractClause, new_c: ContractClause) -> DetailedClauseChange:
        change = DetailedClauseChange(old_c.clause_id, ChangeCategory.PARAMETER_VALUE_CHANGED, ChangeImpact.UNKNOWN, old_c, new_c)
        
        if old_c.clause_type == ClauseType.NULLABILITY:
            change.impact = self.null_analyzer.analyze_impact(old_c, new_c)
            change.description = "Modification of nullability constraints."
        elif old_c.clause_type == ClauseType.SIZE:
            change.impact = self.size_analyzer.analyze_impact(old_c, new_c)
            change.description = "Modification of size/length constraints."
        elif old_c.clause_type == ClauseType.OWNERSHIP:
            change.impact = self.own_analyzer.analyze_impact(old_c, new_c)
            change.description = "Modification of memory ownership model."
        else:
            change.description = f"Modification of {old_c.clause_type.value} constraints."
            
        return change

    def _build_migration_guide(self, result: AdvancedDiffResult) -> MigrationGuide:
        guide = MigrationGuide(result.old_version, result.new_version)
        for change in result.get_breaking_changes():
            if not change.old_clause or not change.new_clause: continue
            if change.old_clause.clause_type == ClauseType.NULLABILITY:
                step = self.null_analyzer.generate_migration_step(change.old_clause, change.new_clause)
                if step: guide.add_step(step)
        
        count = len(guide.steps)
        guide.estimated_effort = "Low" if count < 3 else ("Medium" if count < 6 else "High")
        return guide

__all__ = [
    'ChangeCategory', 'ChangeImpact', 'MigrationDifficulty', 
    'ParameterChange', 'DetailedClauseChange', 'MigrationStep', 
    'MigrationGuide', 'AdvancedDiffResult', 'NullabilityChangeAnalyzer', 
    'SizeChangeAnalyzer', 'OwnershipChangeAnalyzer', 'AdvancedContractDiffer'
]
