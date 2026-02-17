"""
Language Adapter - Runtime FFI Enforcement System

A production-ready Python library for enforcing FFI contracts at runtime.
Provides validation, memory safety, ownership tracking, and comprehensive
observability for foreign function calls.

Version: 1.0.0
"""

__version__ = '1.0.0'
__author__ = 'Module 08 Team'

# ════════════════════════════════════════════════════════════════════════════
# PUBLIC API - HIGH LEVEL
# ════════════════════════════════════════════════════════════════════════════

from .language_adapter import (
    # Main adapter class
    PythonAdapterComplete as LanguageAdapter,
    
    # Validation
    ValidationGraph,
    ValidationNode,
    ClauseSeverity,
    ValidationEngine,
    
    # Configuration
    AdapterConfiguration,
    EnforcementPolicy,
    PolicyType,
    PerformanceProfile,
    
    # Exceptions
    AdapterException,
    ContractViolationError,
    ParameterViolationError,
    ReturnValueViolationError,
    OwnershipViolationError,
    NativeCrashError,
    SegmentationFaultError,
    AccessViolationError,
    
    # Context
    EnforcementContext,
    EnforcementScope,
    
    # Ownership
    OwnershipKind,
    OwnershipGraph,
    TransferAnnotation,
    
    # Memory Management
    PythonPointerWrapper,
    PythonMemoryManager,
    
    # Introspection
    IntrospectionAPI,
    StateSnapshot,
    ContractMetadata,
)

from .testing_utils import (
    # Testing
    MockFFIFunction,
    BehaviorSimulator,
    # Note: ContractTestBuilder and TestFixtures might need to be verified
    TestFixtures,
)

from .persistence import (
    # Persistence
    PersistenceManager,
    SerializationFormat,
    SchemaVersion,
)

from .observability import (
    # Observability
    ObservabilityManager,
    LogLevel,
    MetricsCollector,
)

# ════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def create_adapter(
    contract_path: str = None,
    config: AdapterConfiguration = None
) -> LanguageAdapter:
    """
    Create configured language adapter.
    
    Args:
        contract_path: Optional path to contract file
        config: Optional adapter configuration
        
    Returns:
        Configured LanguageAdapter instance
        
    Example:
        >>> adapter = create_adapter('contract.json')
        >>> result = adapter.call_with_enforcement('my_func', arg1, arg2)
    """
    adapter = LanguageAdapter(config=config)
    
    if contract_path:
        adapter.load_contract(contract_path)
    
    return adapter


def load_contract(path: str) -> dict:
    """
    Load contract from file.
    
    Args:
        path: Path to contract JSON file
        
    Returns:
        Contract dictionary
        
    Example:
        >>> contract = load_contract('contract.json')
        >>> print(contract['contract_id'])
    """
    import json
    with open(path, 'r') as f:
        return json.load(f)


def enforce_contract(contract_path: str):
    """
    Decorator for contract enforcement.
    
    Args:
        contract_path: Path to contract file
        
    Returns:
        Decorator function
        
    Example:
        >>> @enforce_contract('contract.json')
        ... def my_function(adapter, arg1, arg2):
        ...     return adapter.call_with_enforcement('my_func', arg1, arg2)
    """
    def decorator(func):
        adapter = create_adapter(contract_path)
        
        def wrapper(*args, **kwargs):
            return func(adapter, *args, **kwargs)
        
        return wrapper
    
    return decorator


# ════════════════════════════════════════════════════════════════════════════
# MODULE METADATA
# ════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Main
    'LanguageAdapter',
    'create_adapter',
    'load_contract',
    'enforce_contract',
    
    # Core
    'ValidationGraph',
    'ValidationNode',
    'ClauseSeverity',
    'AdapterConfiguration',
    'EnforcementPolicy',
    'PolicyType',
    'PerformanceProfile',
    
    # Exceptions
    'AdapterException',
    'ContractViolationError',
    'NativeCrashError',
    
    # Context
    'EnforcementContext',
    'EnforcementScope',
    
    # Advanced
    'OwnershipGraph',
    'PythonMemoryManager',
    'IntrospectionAPI',
    
    # Utilities
    'MockFFIFunction',
    'PersistenceManager',
    'ObservabilityManager',
]
