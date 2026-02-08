"""
Module 05: IR Normalization
"""

from .ir_orchestrator import IROrchestrator, IRNormalizationConfig
from .module_04_bridge import Module04Bridge
from .type_normalization import TypeNormalizationPipeline
from .ir_validation import IRValidationOrchestrator
from .diagnostics import DiagnosticCollector
from .ir_entities import IREntity, EntityKind, InterfaceUnit
from .ir_serialization import IRArtifact

__all__ = [
    'IROrchestrator',
    'IRNormalizationConfig',
    'Module04Bridge',
    'TypeNormalizationPipeline',
    'IRValidationOrchestrator',
    'DiagnosticCollector',
    'IREntity',
    'EntityKind',
    'InterfaceUnit',
    'IRArtifact'
]
