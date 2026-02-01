"""
Contract Management Module
Handles schema versioning, comparison, and evolution of FFI contracts.
"""

from .schema_validator import ContractSchemaValidator
from .contract_comparator import ContractComparator
from .change_classifier import ChangeClassifier
from .compatibility_report_generator import CompatibilityReportGenerator
from .schema_version_manager import SchemaVersionManager

__all__ = [
    'ContractSchemaValidator',
    'ContractComparator',
    'ChangeClassifier',
    'CompatibilityReportGenerator',
    'SchemaVersionManager'
]
