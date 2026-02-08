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

# Core orchestration
from .ir_orchestrator import (
    IROrchestrator,
    IRNormalizationConfig,
    OrchestrationReport,
    OrchestrationError,
)

# Entity model
from .ir_entities import (
    InterfaceUnit,
    ScalarType,
    PointerType,
    ArrayType,
    StructureType,
    UnionType,
    EnumerationType,
    FunctionPointerType,
    FunctionSymbol,
    VariableSymbol,
)

# Validation
from .ir_validation import (
    IRValidationOrchestrator,
    ValidationReport,
)

# Serialization
from .ir_serialization import (
    IRArtifact,
    IRArtifactManager,
)

# Diffing
from .ir_diff import (
    IRDiffComputer,
    IRDiff,
    recommend_version_bump,
)

# Integration Bridge
from .module_04_bridge import (
    Module04Bridge,
    TypeDeduplicator,
    TypeConverter,
    SymbolConverter,
)

# Diagnostics
from .diagnostics import (
    DiagnosticCollector,
    DiagnosticMessage,
    Severity,
)

__all__ = [
    # Version
    '__version__',
    '__version_info__',
    'get_version',
    
    # Orchestration
    'IROrchestrator',
    'IRNormalizationConfig',
    'OrchestrationReport',
    'OrchestrationError',
    
    # Entities
    'InterfaceUnit',
    'ScalarType',
    'PointerType',
    'ArrayType',
    'StructureType',
    'UnionType',
    'EnumerationType',
    'FunctionPointerType',
    'FunctionSymbol',
    'VariableSymbol',
    
    # Validation
    'IRValidationOrchestrator',
    'ValidationReport',
    
    # Serialization
    'IRArtifact',
    'IRArtifactManager',
    
    # Diffing
    'IRDiffComputer',
    'IRDiff',
    'recommend_version_bump',
    
    # Diagnostics
    'DiagnosticCollector',
    'DiagnosticMessage',
    'Severity',
    
    # Integration Bridge
    'Module04Bridge',
    'TypeDeduplicator',
    'TypeConverter',
    'SymbolConverter',
]

# Module metadata
__author__ = "PFCV Authors"
__email__ = "team@pfcv.dev"
__license__ = "MIT"
__copyright__ = "Copyright 2025 PFCV Authors"
