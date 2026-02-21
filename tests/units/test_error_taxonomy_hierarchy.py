import pytest
from modules.module_08_language_adapter.language_adapter import (
    AdapterRuntimeError,
    EnforcementError,
    ContractViolationError,
    StructureLayoutMismatchError,
    NativeCrashError,
    ErrorTaxonomyManager,
    EnforcementContext,
    ContractMetadata
)

def test_error_hierarchy_inheritance():
    """Ensure all core adapter errors inherit from the canonical root class."""
    assert issubclass(EnforcementError, AdapterRuntimeError)
    assert issubclass(ContractViolationError, AdapterRuntimeError)
    assert issubclass(StructureLayoutMismatchError, AdapterRuntimeError)
    assert issubclass(NativeCrashError, AdapterRuntimeError)

def test_error_code_mapping():
    """Ensure ErrorTaxonomyManager maps exceptions correctly."""
    ctx = EnforcementContext("F1", ContractMetadata("1.0", "1.0", "F1", 64, {}))
    
    # Test known error
    err = ContractViolationError("func", 0, "msg", "F1")
    code, category = ctx.error_taxonomy.classify(err)
    assert code == "ERR_CONTRACT_VIOLATION"
    assert category == "Enforcement"
    
    # Test unknown error fail-closed logic
    unk_err = ValueError("Something unexpected")
    code, category = ctx.error_taxonomy.classify(unk_err)
    assert code == "ERR_INTERNAL_UNKNOWN"
    assert category == "Internal"
