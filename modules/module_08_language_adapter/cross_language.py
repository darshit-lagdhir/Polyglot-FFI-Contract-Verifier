""" Cross-Language Contract Sharing and Interoperability.

Enables contracts to be shared across Python, Rust, C++, and other languages. """

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# ════════════════════════════════════════════════════════════════════════════
# SECTION 125: UNIVERSAL TYPE SYSTEM
# ════════════════════════════════════════════════════════════════════════════

class UniversalType(Enum):
    """Universal types for cross-language compatibility."""
    # Primitives
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    BOOL = "bool"
    CHAR = "char"

    # Compound types
    BUFFER = "buffer"
    STRING = "string"
    ARRAY = "array"

    # Special types
    POINTER = "pointer"
    OPTIONAL = "optional"
    RESULT = "result"
    VOID = "void"

class UniversalOwnership(Enum):
    """Universal ownership semantics."""
    TRANSFER_TO_CALLER = "transfer_to_caller"
    TRANSFER_TO_CALLEE = "transfer_to_callee"
    BORROW_IMMUTABLE = "borrow_immutable"
    BORROW_MUTABLE = "borrow_mutable"
    SHARED = "shared"
    COPY = "copy"

@dataclass
class UniversalTypeDescriptor:
    """Describes a type in universal terms."""
    base_type: UniversalType
    ownership: UniversalOwnership = UniversalOwnership.COPY
    is_nullable: bool = False
    type_params: List['UniversalTypeDescriptor'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'base_type': self.base_type.value,
            'ownership': self.ownership.value,
            'is_nullable': self.is_nullable,
            'type_params': [tp.to_dict() for tp in self.type_params]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UniversalTypeDescriptor':
        """Create from dictionary."""
        return UniversalTypeDescriptor(
            base_type=UniversalType(data['base_type']),
            ownership=UniversalOwnership(data['ownership']),
            is_nullable=data.get('is_nullable', False),
            type_params=[
                UniversalTypeDescriptor.from_dict(tp)
                for tp in data.get('type_params', [])
            ]
        )

# ════════════════════════════════════════════════════════════════════════════
# SECTION 126: UNIVERSAL CONTRACT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class UniversalParameter:
    """Universal parameter descriptor."""
    name: str
    type_descriptor: UniversalTypeDescriptor
    clauses: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.type_descriptor.to_dict(),
            'clauses': self.clauses
        }

@dataclass
class UniversalFunction:
    """Universal function descriptor."""
    name: str
    parameters: List[UniversalParameter]
    return_type: UniversalTypeDescriptor
    clauses: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'parameters': [p.to_dict() for p in self.parameters],
            'return_type': self.return_type.to_dict(),
            'clauses': self.clauses
        }

@dataclass
class UniversalContract:
    """ Language-agnostic contract representation.

    Can be projected to any language adapter.
    """
    contract_id: str
    abi_version: str
    supported_languages: List[str]
    functions: Dict[str, UniversalFunction]
    compatibility: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'contract_id': self.contract_id,
            'abi_version': self.abi_version,
            'supported_languages': self.supported_languages,
            'functions': {
                name: func.to_dict()
                for name, func in self.functions.items()
            },
            'compatibility': self.compatibility
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UniversalContract':
        """Create from dictionary."""
        functions = {}
        
        for name, func_data in data.get('functions', {}).items():
            parameters = [
                UniversalParameter(
                    name=p['name'],
                    type_descriptor=UniversalTypeDescriptor.from_dict(p['type']),
                    clauses=p.get('clauses', [])
                )
                for p in func_data.get('parameters', [])
            ]
            
            functions[name] = UniversalFunction(
                name=func_data['name'],
                parameters=parameters,
                return_type=UniversalTypeDescriptor.from_dict(
                    func_data['return_type']
                ),
                clauses=func_data.get('clauses', [])
            )
        
        return UniversalContract(
            contract_id=data['contract_id'],
            abi_version=data['abi_version'],
            supported_languages=data.get('supported_languages', []),
            functions=functions,
            compatibility=data.get('compatibility', {})
        )

# ════════════════════════════════════════════════════════════════════════════
# SECTION 127: TYPE PROJECTOR
# ════════════════════════════════════════════════════════════════════════════

class TypeProjector:
    """ Projects universal types to language-specific types.

    Handles type mapping for each supported language.
    """

    def __init__(self, language: str):
        self.language = language
        self._init_type_mappings()

    def _init_type_mappings(self):
        """Initialize type mappings for language."""
        # Python type mappings
        self.python_types = {
            UniversalType.INT32: 'int',
            UniversalType.INT64: 'int',
            UniversalType.UINT32: 'int',
            UniversalType.UINT64: 'int',
            UniversalType.FLOAT32: 'float',
            UniversalType.FLOAT64: 'float',
            UniversalType.BOOL: 'bool',
            UniversalType.STRING: 'str',
            UniversalType.BUFFER: 'bytes',
            UniversalType.OPTIONAL: 'Optional',
            UniversalType.VOID: 'None',
        }
        
        # Rust type mappings
        self.rust_types = {
            UniversalType.INT32: 'i32',
            UniversalType.INT64: 'i64',
            UniversalType.UINT32: 'u32',
            UniversalType.UINT64: 'u64',
            UniversalType.FLOAT32: 'f32',
            UniversalType.FLOAT64: 'f64',
            UniversalType.BOOL: 'bool',
            UniversalType.STRING: 'String',
            UniversalType.BUFFER: '&[u8]',
            UniversalType.OPTIONAL: 'Option',
            UniversalType.VOID: '()',
        }
        
        # C++ type mappings
        self.cpp_types = {
            UniversalType.INT32: 'int32_t',
            UniversalType.INT64: 'int64_t',
            UniversalType.UINT32: 'uint32_t',
            UniversalType.UINT64: 'uint64_t',
            UniversalType.FLOAT32: 'float',
            UniversalType.FLOAT64: 'double',
            UniversalType.BOOL: 'bool',
            UniversalType.STRING: 'std::string',
            UniversalType.BUFFER: 'std::span<uint8_t>',
            UniversalType.OPTIONAL: 'std::optional',
            UniversalType.VOID: 'void',
        }

    def project_type(
        self,
        universal_type: UniversalTypeDescriptor
    ) -> str:
        """
        Project universal type to language-specific type.
        
        Args:
            universal_type: Universal type descriptor
            
        Returns:
            Language-specific type string
        """
        if self.language == 'python':
            return self._project_python(universal_type)
        elif self.language == 'rust':
            return self._project_rust(universal_type)
        elif self.language == 'cpp':
            return self._project_cpp(universal_type)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _project_python(
        self,
        universal_type: UniversalTypeDescriptor
    ) -> str:
        """Project to Python type."""
        base = self.python_types.get(universal_type.base_type, 'Any')
        
        if universal_type.is_nullable:
            base = f"Optional[{base}]"
        
        return base

    def _project_rust(
        self,
        universal_type: UniversalTypeDescriptor
    ) -> str:
        """Project to Rust type."""
        base = self.rust_types.get(universal_type.base_type, 'unknown')
        
        # Handle ownership
        if universal_type.ownership == UniversalOwnership.BORROW_IMMUTABLE:
            base = f"&{base}"
        elif universal_type.ownership == UniversalOwnership.BORROW_MUTABLE:
            base = f"&mut {base}"
        
        # Handle nullable
        if universal_type.is_nullable:
            base = f"Option<{base}>"
        
        return base

    def _project_cpp(
        self,
        universal_type: UniversalTypeDescriptor
    ) -> str:
        """Project to C++ type."""
        base = self.cpp_types.get(universal_type.base_type, 'void*')
        
        # Handle ownership
        if universal_type.ownership == UniversalOwnership.BORROW_IMMUTABLE:
            base = f"const {base}&"
        elif universal_type.ownership == UniversalOwnership.BORROW_MUTABLE:
            base = f"{base}&"
        elif universal_type.ownership == UniversalOwnership.TRANSFER_TO_CALLER:
            base = f"std::unique_ptr<{base}>"
        
        # Handle nullable
        if universal_type.is_nullable:
            base = f"std::optional<{base}>"
        
        return base

# ════════════════════════════════════════════════════════════════════════════
# SECTION 128: COMPATIBILITY CHECKER
# ════════════════════════════════════════════════════════════════════════════

class CompatibilityChecker:
    """ Checks language compatibility for contracts.

    Validates that contract requirements match language capabilities.
    """

    def check_compatibility(
        self,
        contract: UniversalContract,
        language: str,
        language_version: str
    ) -> Tuple[bool, List[str]]:
        """
        Check if language is compatible with contract.
        
        Args:
            contract: Universal contract
            language: Language name
            language_version: Language version
            
        Returns:
            Tuple of (is_compatible, error_messages)
        """
        errors = []
        
        # Check if language is supported
        if language not in contract.supported_languages:
            errors.append(f"Language '{language}' not supported by contract")
            return (False, errors)
        
        # Check version requirements
        if language in contract.compatibility:
            compat = contract.compatibility[language]
            
            # Check minimum version
            if 'min_version' in compat:
                if not self._version_gte(language_version, compat['min_version']):
                    errors.append(
                        f"Language version {language_version} < "
                        f"minimum {compat['min_version']}"
                    )
            
            # Check maximum version
            if 'max_version' in compat:
                if not self._version_lte(language_version, compat['max_version']):
                    errors.append(
                        f"Language version {language_version} > "
                        f"maximum {compat['max_version']}"
                    )
        
        return (len(errors) == 0, errors)

    def _version_gte(self, version: str, min_version: str) -> bool:
        """Check if version >= min_version."""
        try:
            v_parts = [int(p) for p in version.split('.')]
            min_parts = [int(p) for p in min_version.split('.')]
            
            for v, m in zip(v_parts, min_parts):
                if v > m:
                    return True
                elif v < m:
                    return False
            
            return len(v_parts) >= len(min_parts)
        except (ValueError, AttributeError):
            return False

    def _version_lte(self, version: str, max_version: str) -> bool:
        """Check if version <= max_version."""
        try:
            v_parts = [int(p) for p in version.split('.')]
            max_parts = [int(p) for p in max_version.split('.')]
            
            for v, m in zip(v_parts, max_parts):
                if v < m:
                    return True
                elif v > m:
                    return False
            
            return len(v_parts) <= len(max_parts)
        except (ValueError, AttributeError):
            return False

# ════════════════════════════════════════════════════════════════════════════
# SECTION 129: CONTRACT TRANSLATOR
# ════════════════════════════════════════════════════════════════════════════

class ContractTranslator:
    """ Translates between universal and language-specific contracts.

    Converts universal contracts to Python/Rust/C++ contracts.
    """

    def __init__(self, language: str):
        self.language = language
        self.type_projector = TypeProjector(language)

    def translate_to_language(
        self,
        universal_contract: UniversalContract
    ) -> Dict[str, Any]:
        """
        Translate universal contract to language-specific format.
        
        Args:
            universal_contract: Universal contract
            
        Returns:
            Language-specific contract dictionary
        """
        language_contract = {
            'contract_id': universal_contract.contract_id,
            'schema_version': universal_contract.abi_version,
            'language': self.language,
            'functions': {}
        }
        
        for func_name, func in universal_contract.functions.items():
            language_contract['functions'][func_name] = {
                'name': func_name,
                'parameters': [
                    {
                        'name': param.name,
                        'type': self.type_projector.project_type(
                            param.type_descriptor
                        ),
                        'clauses': param.clauses
                    }
                    for param in func.parameters
                ],
                'return': {
                    'type': self.type_projector.project_type(func.return_type)
                },
                'clauses': func.clauses
            }
        
        return language_contract

# ════════════════════════════════════════════════════════════════════════════
# SECTION 130: INTEROP REGISTRY
# ════════════════════════════════════════════════════════════════════════════

class InteropRegistry:
    """ Registry of cross-language adapters.

    Manages adapters for different languages using shared contracts.
    """

    def __init__(self):
        self.adapters: Dict[str, Any] = {}
        self.contracts: Dict[str, UniversalContract] = {}

    def register_adapter(
        self,
        language: str,
        adapter: Any
    ) -> None:
        """
        Register language adapter.
        
        Args:
            language: Language name
            adapter: Language adapter instance
        """
        self.adapters[language] = adapter

    def register_contract(
        self,
        contract: UniversalContract
    ) -> None:
        """
        Register universal contract.
        
        Args:
            contract: Universal contract
        """
        self.contracts[contract.contract_id] = contract

    def get_adapter(self, language: str) -> Optional[Any]:
        """Get adapter for language."""
        return self.adapters.get(language)

    def get_contract(self, contract_id: str) -> Optional[UniversalContract]:
        """Get contract by ID."""
        return self.contracts.get(contract_id)

    def get_language_contract(
        self,
        contract_id: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get contract translated for specific language.
        
        Args:
            contract_id: Contract ID
            language: Target language
            
        Returns:
            Language-specific contract or None
        """
        universal = self.contracts.get(contract_id)
        if not universal:
            return None
        
        translator = ContractTranslator(language)
        return translator.translate_to_language(universal)

# Export cross-language components
__all__ = [
    'UniversalType',
    'UniversalOwnership',
    'UniversalTypeDescriptor',
    'UniversalParameter',
    'UniversalFunction',
    'UniversalContract',
    'TypeProjector',
    'CompatibilityChecker',
    'ContractTranslator',
    'InteropRegistry',
]
