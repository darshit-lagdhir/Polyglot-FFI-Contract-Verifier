"""
Module 07: IR Bridge (Prompt 4/15)

Bridge between Module 05 (IR Normalization) and Module 07 (Synthesis Engine).

Responsibilities:
- Validate IR artifacts
- Transform IR entities to synthesis format
- Handle errors gracefully
- Maintain traceability
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import logging

# Module 05 imports
from module_05_ir_normalization.ir_entities import (
    InterfaceUnit, TypeEntity, FunctionSymbol, ParameterEntity, 
    EntityKind, StructureType, UnionType, PointerType, ArrayType,
    FieldEntity
)

logger = logging.getLogger(__name__)

# ============================================================================
# BRIDGE EXCEPTIONS
# ============================================================================

class IRBridgeError(Exception):
    """Base exception for IR bridge errors."""
    pass

class TypeCompletenessError(IRBridgeError):
    """Raised when referenced types are not defined."""
    pass

class SignatureCoherenceError(IRBridgeError):
    """Raised when function signature is incoherent."""
    pass

class ABIMetadataError(IRBridgeError):
    """Raised when ABI metadata is invalid."""
    pass

# ============================================================================
# IR VALIDATION
# ============================================================================

@dataclass
class IRValidationResult:
    """Result of IR validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
        
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)

class IRValidator:
    """
    Validates IR artifacts before synthesis.
    
    Ensures IR meets synthesis requirements and catches common issues.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate(self, ir_unit: InterfaceUnit) -> IRValidationResult:
        """
        Comprehensive IR validation.
        
        Args:
            ir_unit: IR interface unit to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = IRValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate type completeness
        self._validate_type_completeness(ir_unit, result)
        
        # Validate function signatures
        self._validate_function_signatures(ir_unit, result)
        
        # Validate ABI metadata (if present)
        self._validate_abi_metadata(ir_unit, result)
        
        # Check for common issues
        self._check_common_issues(ir_unit, result)
        
        return result
        
    def _validate_type_completeness(
        self,
        ir_unit: InterfaceUnit,
        result: IRValidationResult
    ):
        """Validate all referenced types are defined."""
        # Use entity_id as the key for defined types
        defined_types = {t.entity_id for t in ir_unit.types}
        referenced_types = set()
        
        # Collect referenced types from functions
        for func in ir_unit.symbols:
            if isinstance(func, FunctionSymbol):
                # Parameters
                if func.parameters:
                    for param in func.parameters:
                        if param.type_reference:
                            referenced_types.add(param.type_reference)
                
                # Return type (if represented as entity/field/reference)
                # In IR, return type is usually encoded in FieldEntity or similar if structured return
                # But FunctionSymbol structure has changed across prompts. 
                # Checking recent usage: FunctionSymbol has return_entity which is FieldEntity logic.
                if hasattr(func, 'return_entity') and func.return_entity:
                    if func.return_entity.type_reference:
                         referenced_types.add(func.return_entity.type_reference)

        # Collect referenced types from Type definitions (nested types)
        for t in ir_unit.types:
            if isinstance(t, StructureType):
                for f in t.fields:
                    referenced_types.add(f.type_reference)
            elif isinstance(t, UnionType):
                for m in t.members:
                    referenced_types.add(m.type_reference)
            elif isinstance(t, PointerType):
                referenced_types.add(t.target_type_reference)
            elif isinstance(t, ArrayType):
                referenced_types.add(t.element_type_reference)

        # Find missing types
        missing = referenced_types - defined_types
        
        # Filter out built-in types - this list needs to match what synthesis considers builtin
        # or references to primitives that might not be explicitly in 'types' list if Module 05 handles them implicitly.
        # However, usually ScalarTypes are in the type list.
        # We'll allow standard C types just in case they aren't explicit entities.
        builtin_types = {
            "int", "long", "float", "double", "void", "char", "short",
            "signed int", "unsigned int", "signed long", "unsigned long",
            "int8_t", "uint8_t", "int16_t", "uint16_t",
            "int32_t", "uint32_t", "int64_t", "uint64_t", "size_t",
            "void*", "char*" # basic pointers often treated as atomic
        }
        
        # Also filter out likely specific pointers if their base is missing but we want to be linient? NO.
        # But referenced_types contains strings like "MyStruct*".
        # If "MyStruct*" is in defined_types (explicit PointerType), good.
        # If not, it's missing.
        
        missing = missing - builtin_types
        
        # Filter valid pointer types that might be implicit? 
        # Module 05 requires explicit PointerType entities usually.
        # But let's check if we should ignore * suffix for basic checks if strictness is concern.
        # The prompt says: "Every type referenced... must have a corresponding type definition".
        # So stricter is better.
        
        if missing:
            # We add error, but maybe warn if it looks like a system header type?
            # For now, stick to the plan.
            result.add_error(
                f"Missing type definitions: {', '.join(sorted(missing))}"
            )
            
    def _validate_function_signatures(
        self,
        ir_unit: InterfaceUnit,
        result: IRValidationResult
    ):
        """Validate function signatures are coherent."""
        for func in ir_unit.symbols:
            if not isinstance(func, FunctionSymbol):
                continue
                
            # Check for duplicate parameter names
            if func.parameters:
                param_names = [p.parameter_name for p in func.parameters if p.parameter_name]
                duplicates = [name for name in param_names if param_names.count(name) > 1]
                
                if duplicates:
                    # distinct duplicates
                    duplicates = list(set(duplicates)) 
                    result.add_error(
                        f"Function {func.entity_id} has duplicate parameter names: {duplicates}"
                    )
                
                # Check for empty parameter names (warning)
                if any(not p.parameter_name for p in func.parameters):
                    # Sometimes params are unnamed in C prototypes, but IR should have them?
                    # Module 05 might generate param_0, param_1.
                    # If empty, it's a warning.
                    result.add_warning(
                        f"Function {func.entity_id} has parameters with empty names"
                    )

    def _validate_abi_metadata(
        self,
        ir_unit: InterfaceUnit,
        result: IRValidationResult
    ):
        """Validate ABI metadata if present."""
        # InterfaceUnit might have metadata field, or specific fields.
        # It has target_architecture, etc.
        # The prompt mentions 'abi_metadata'.
        # Let's check getattr.
        abi_metadata = getattr(ir_unit, 'metadata', None)
        
        if not abi_metadata:
            return
            
        # If metadata is MetadataEntity, it has generic fields.
        # Prompt probably implies specific ABI info.
        # InterfaceUnit has: target_architecture, pointer_width, abi_mode, etc.
        # We can validate those.
        
        if not ir_unit.target_architecture:
            result.add_warning("Missing target architecture")
        if not ir_unit.pointer_width:
             result.add_warning("Missing pointer width")

    def _check_common_issues(
        self,
        ir_unit: InterfaceUnit,
        result: IRValidationResult
    ):
        """Check for common IR issues."""
        # Warn if no functions
        # ir_unit.symbols contains functions and globals?
        functions = [s for s in ir_unit.symbols if isinstance(s, FunctionSymbol)]
        if not functions:
            result.add_warning("IR contains no functions")
        
        # Warn if no types
        if not ir_unit.types:
            result.add_warning("IR contains no type definitions")

# ============================================================================
# IR TRANSFORMATION
# ============================================================================

class IRBridge:
    """
    Main IR bridge between Module 05 and Module 07.
    
    Validates and transforms IR artifacts for synthesis.
    """
    
    def __init__(self):
        self.validator = IRValidator()
        self.logger = logging.getLogger(__name__)
        
    def consume_ir(
        self,
        ir_unit: InterfaceUnit,
        strict: bool = True
    ) -> InterfaceUnit:
        """
        Consume and validate IR artifact.
        
        Args:
            ir_unit: IR interface unit from Module 05
            strict: If True, raise on validation errors
            
        Returns:
            Validated IR unit (may be modified for compatibility)
            
        Raises:
            IRBridgeError: If validation fails in strict mode
        """
        self.logger.info(f"Consuming IR artifact: {ir_unit.entity_id}")
        
        # Validate
        validation_result = self.validator.validate(ir_unit)
        
        # Log warnings
        for warning in validation_result.warnings:
            self.logger.warning(f"IR validation warning: {warning}")
        
        # Handle errors
        if not validation_result.is_valid:
            error_msg = "\n".join(validation_result.errors)
            
            if strict:
                raise IRBridgeError(f"IR validation failed:\n{error_msg}")
            else:
                self.logger.error(f"IR validation errors (continuing): {error_msg}")
        
        # Transform if needed (currently pass-through)
        transformed = self._transform_ir(ir_unit)
        
        func_count = sum(1 for s in transformed.symbols if isinstance(s, FunctionSymbol))
        self.logger.info(f"IR artifact consumed successfully: {func_count} functions")
        
        return transformed
        
    def _transform_ir(self, ir_unit: InterfaceUnit) -> InterfaceUnit:
        """
        Transform IR for synthesis (currently pass-through).
        
        Future: May adapt older IR versions or optimize representations.
        """
        return ir_unit
