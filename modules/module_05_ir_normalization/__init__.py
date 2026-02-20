# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 1babf020001964aa
# ==============================================================================

"""
PFCV Module 05: IR Normalization

Transform raw interface artifacts into canonical intermediate representation.

This module provides:
    - Complete IR entity model
- Type and symbol normalization
- Validation framework
- Serialization and caching
- ABI change detection
- CLI interface

Quick Start:
    >>> from module_05_ir_normalization import IROrchestrator, IRNormalizationConfig
    >>> config = IRNormalizationConfig(input_artifact_path="input.json")
    >>> orchestrator = IROrchestrator(config)
    >>> report = orchestrator.execute()
"""

from .__version__ import __version__, __version_info__, get_version

# Diagnostics
from .diagnostics import (
    DiagnosticCollector,
    DiagnosticMessage,
    IRSeverity as Severity,
)

# Diffing
from .ir_diff import (
    IRDiff,
    IRDiffComputer,
    recommend_version_bump,
)

# Entity model
from .ir_entities import (
    ArrayType,
    EnumerationType,
    FunctionPointerType,
    FunctionSymbol,
    InterfaceUnit,
    PointerType,
    ScalarType,
    StructureType,
    UnionType,
    VariableSymbol,
)

# Core orchestration
from .ir_orchestrator import (
    IRNormalizationConfig,
    IROrchestrator,
    OrchestrationError,
    OrchestrationReport,
)

# Serialization
from .ir_serialization import (
    IRArtifact,
    IRArtifactManager,
)

# Validation
from .ir_validation import (
    IRValidationOrchestrator,
    ValidationReport,
)

# Integration Bridge
from .module_04_bridge import (
    Module04Bridge,
    SymbolConverter,
    TypeConverter,
    TypeDeduplicator,
)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    "get_version",
    # Orchestration
    "IROrchestrator",
    "IRNormalizationConfig",
    "OrchestrationReport",
    "OrchestrationError",
    # Entities
    "InterfaceUnit",
    "ScalarType",
    "PointerType",
    "ArrayType",
    "StructureType",
    "UnionType",
    "EnumerationType",
    "FunctionPointerType",
    "FunctionSymbol",
    "VariableSymbol",
    # Validation
    "IRValidationOrchestrator",
    "ValidationReport",
    # Serialization
    "IRArtifact",
    "IRArtifactManager",
    # Diffing
    "IRDiffComputer",
    "IRDiff",
    "recommend_version_bump",
    # Diagnostics
    "DiagnosticCollector",
    "DiagnosticMessage",
    "Severity",
    # Integration Bridge
    "Module04Bridge",
    "TypeDeduplicator",
    "TypeConverter",
    "SymbolConverter",
]

# Module metadata
__author__ = "PFCV Authors"
__email__ = "team@pfcv.dev"
__license__ = "MIT"
__copyright__ = "Copyright 2025 PFCV Authors"