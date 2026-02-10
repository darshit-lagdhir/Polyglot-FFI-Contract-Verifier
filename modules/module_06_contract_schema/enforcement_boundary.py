"""
Module 06: Contract Schema - Enforcement Boundary

Enforcement boundary and language adapter interface for runtime contract checking.
Separates declarative contracts from imperative language-specific enforcement.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, List, NoReturn
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
import time
import logging

from .contract_entities import (
    ContractDocument, ContractClause, ClauseType, Severity
)

# ============================================================================
# ENFORCEMENT ENUMS
# ============================================================================

class EnforcementMode(Enum):
    """Enforcement mode."""
    STRICT = "strict"           # All violations are fatal
    PRODUCTION = "production"   # Only ERROR severity enforced
    AUDIT = "audit"             # Log violations, don't fail
    DISABLED = "disabled"       # No enforcement

class ViolationType(Enum):
    """Type of constraint violation."""
    NULLABILITY = "nullability"
    SIZE = "size"
    ALIGNMENT = "alignment"
    LAYOUT = "layout"
    OWNERSHIP = "ownership"
    LIFETIME = "lifetime"
    RELATIONAL = "relational"
    CALLING_CONVENTION = "calling_convention"

# ============================================================================
# ENFORCEMENT VIOLATION
# ============================================================================

@dataclass
class EnforcementViolation:
    """Runtime constraint violation."""
    
    clause_id: str
    violation_type: ViolationType
    entity_id: str
    
    expected: Any
    actual: Any
    
    severity: Severity
    timestamp: str = ""
    
    call_context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
            
    def format_error_message(self) -> str:
        """Generate human-readable error message."""
        lines = [
            f"Contract Violation: {self.violation_type.value}",
            "",
            f"Clause: {self.clause_id}",
            f"Entity: {self.entity_id}",
            f"Severity: {self.severity.value.upper()}",
            "",
            f"Expected: {self.expected}",
            f"Actual: {self.actual}",
        ]
        
        if self.call_context:
            lines.append("")
            lines.append("Context:")
            for key, value in self.call_context.items():
                lines.append(f"  {key}: {value}")
                
        lines.append("")
        lines.append("This violation indicates the FFI call does not satisfy the contract.")
        lines.append("Review the contract clause and ensure calling code meets requirements.")
        
        return "\n".join(lines)

# ============================================================================
# ENFORCEMENT STATISTICS
# ============================================================================

@dataclass
class EnforcementStats:
    """Runtime enforcement statistics."""
    
    total_calls: int = 0
    total_violations: int = 0
    violations_by_type: Dict[str, int] = field(default_factory=dict)
    
    enforcement_time_ns: int = 0
    
    def record_call(self):
        """Record FFI call."""
        self.total_calls += 1
        
    def record_violation(self, violation: EnforcementViolation):
        """Record violation."""
        self.total_violations += 1
        
        vtype = violation.violation_type.value
        self.violations_by_type[vtype] = self.violations_by_type.get(vtype, 0) + 1
        
    def record_enforcement_time(self, time_ns: int):
        """Record enforcement overhead."""
        self.enforcement_time_ns += time_ns
        
    def get_violation_rate(self) -> float:
        """Get violation rate."""
        if self.total_calls == 0:
            return 0.0
        return self.total_violations / self.total_calls
        
    def get_average_overhead_ns(self) -> float:
        """Get average enforcement overhead."""
        if self.total_calls == 0:
            return 0.0
        return self.enforcement_time_ns / self.total_calls
        
    def report(self) -> str:
        """Generate statistics report."""
        lines = [
            "Enforcement Statistics",
            "=" * 80,
            "",
            f"Total Calls: {self.total_calls}",
            f"Total Violations: {self.total_violations}",
            f"Violation Rate: {self.get_violation_rate():.2%}",
            f"Avg Overhead: {self.get_average_overhead_ns():.1f}ns per call",
        ]
        
        if self.violations_by_type:
            lines.append("")
            lines.append("Violations by Type:")
            for vtype, count in sorted(self.violations_by_type.items()):
                lines.append(f"  {vtype}: {count}")
                
        return "\n".join(lines)

# ============================================================================
# LANGUAGE ADAPTER INTERFACE
# ============================================================================

class LanguageAdapter(ABC):
    """
    Abstract interface for language-specific enforcement.
    
    Each language (Python, Rust, etc.) implements this interface to provide
    language-specific constraint checking.
    """
    
    @abstractmethod
    def check_nullability(self, ptr: Any, nullable: bool) -> bool:
        """
        Check if pointer satisfies nullability constraint.
        
        Args:
            ptr: Pointer/reference to check
            nullable: Whether null is allowed
            
        Returns:
            True if constraint satisfied
        """
        pass
        
    @abstractmethod
    def check_size(self, buffer: Any, required_size: int) -> bool:
        """
        Check if buffer meets size requirement.
        
        Args:
            buffer: Buffer to check
            required_size: Minimum required size in bytes
            
        Returns:
            True if buffer is large enough
        """
        pass
        
    @abstractmethod
    def check_alignment(self, ptr: Any, alignment: int) -> bool:
        """
        Check if pointer meets alignment requirement.
        
        Args:
            ptr: Pointer to check
            alignment: Required alignment (power of 2)
            
        Returns:
            True if properly aligned
        """
        pass
        
    @abstractmethod
    def check_layout(self, obj: Any, expected_layout: Dict[str, Any]) -> bool:
        """
        Check if object layout matches expected.
        
        Args:
            obj: Object to check
            expected_layout: Expected layout specification
            
        Returns:
            True if layout matches
        """
        pass
        
    @abstractmethod
    def report_violation(self, violation: EnforcementViolation):
        """
        Report constraint violation.
        
        Args:
            violation: Violation details
        """
        pass

# ============================================================================
# PYTHON ADAPTER
# ============================================================================

class PythonAdapter(LanguageAdapter):
    """Python-specific enforcement adapter."""
    
    def __init__(self, mode: EnforcementMode = EnforcementMode.STRICT):
        self.mode = mode
        self.violations: List[EnforcementViolation] = []
        
    def check_nullability(self, ptr: Any, nullable: bool) -> bool:
        """Check nullability constraint."""
        is_none = ptr is None
        
        # If not nullable but is None, violation
        if not nullable and is_none:
            return False
            
        return True
        
    def check_size(self, buffer: Any, required_size: int) -> bool:
        """Check size constraint."""
        # Python bytes/bytearray
        if hasattr(buffer, '__len__'):
            actual_size = len(buffer)
            return actual_size >= required_size
            
        # ctypes buffer
        if hasattr(buffer, '_length_'):
            return buffer._length_ >= required_size
            
        # Cannot verify - conservatively assume valid
        return True
        
    def check_alignment(self, ptr: Any, alignment: int) -> bool:
        """Check alignment constraint."""
        try:
            import ctypes
            
            # If it's a ctypes pointer-like object
            if hasattr(ptr, 'contents'):
                addr = ctypes.addressof(ptr.contents)
                return (addr % alignment) == 0
            
            # If it's a raw address (int)
            if isinstance(ptr, int):
                return (ptr % alignment) == 0
                
            # If it's a c_void_p or similar
            if hasattr(ptr, 'value') and isinstance(ptr.value, int):
                return (ptr.value % alignment) == 0
                
        except:
            pass
            
        # Cannot verify non-ctypes pointers - assume aligned
        return True
        
    def check_layout(self, obj: Any, expected_layout: Dict[str, Any]) -> bool:
        """Check layout constraint."""
        # Layout checking is typically done at binding generation time
        # Runtime checks are limited
        
        expected_size = expected_layout.get('expected_size')
        if expected_size is not None:
            try:
                import ctypes
                if isinstance(obj, ctypes.Structure):
                    return ctypes.sizeof(obj) == expected_size
            except:
                pass
                
        # Assume valid if cannot verify
        return True
        
    def report_violation(self, violation: EnforcementViolation):
        """Report violation."""
        self.violations.append(violation)
        
        if self.mode == EnforcementMode.STRICT:
            # Strict mode: raise exception
            raise RuntimeError(violation.format_error_message())
            
        elif self.mode == EnforcementMode.AUDIT or self.mode == EnforcementMode.PRODUCTION:
            # Log violation
            logging.warning(f"Contract violation: {violation.clause_id} on {violation.entity_id}")

# ============================================================================
# ENFORCEMENT ENGINE
# ============================================================================

class EnforcementEngine:
    """
    Contract enforcement engine.
    
    Orchestrates runtime enforcement using language adapters.
    """
    
    def __init__(
        self,
        contract: ContractDocument,
        adapter: LanguageAdapter,
        mode: EnforcementMode = EnforcementMode.STRICT
    ):
        """
        Initialize enforcement engine.
        
        Args:
            contract: Contract to enforce
            adapter: Language-specific adapter
            mode: Enforcement mode
        """
        self.contract = contract
        self.adapter = adapter
        self.mode = mode
        
        # Build clause index for fast lookup
        self.clause_index = self._build_clause_index()
        
        # Statistics
        self.stats = EnforcementStats()
        
    def _build_clause_index(self) -> Dict[str, List[ContractClause]]:
        """Build index of clauses by entity ID."""
        index: Dict[str, List[ContractClause]] = {}
        
        for clause in self.contract.clauses:
            entity_id = clause.subject_reference.entity_id
            if entity_id not in index:
                index[entity_id] = []
            index[entity_id].append(clause)
            
        return index
        
    def enforce_pre_call(
        self,
        function_id: str,
        args: Dict[str, Any]
    ) -> List[EnforcementViolation]:
        """
        Enforce pre-call constraints.
        
        Args:
            function_id: Function being called
            args: Function arguments (parameter_name -> value)
            
        Returns:
            List of violations (empty if all constraints satisfied)
        """
        violations = []
        
        if self.mode == EnforcementMode.DISABLED:
            return violations
            
        start_time = time.perf_counter_ns()
        self.stats.record_call()
        
        # 1. Enforce function-level clauses (like alignment or calling convention)
        func_clauses = self.clause_index.get(function_id, [])
        for clause in func_clauses:
            # In a real implementation, we would check calling convention etc.
            pass
            
        # 2. Enforce parameter-level clauses
        for param_id, value in args.items():
            param_clauses = self.clause_index.get(param_id, [])
            for clause in param_clauses:
                violation = self._enforce_clause(clause, value, args)
                if violation:
                    violations.append(violation)
                    self.stats.record_violation(violation)
                    self.adapter.report_violation(violation)
                    
        end_time = time.perf_counter_ns()
        self.stats.record_enforcement_time(end_time - start_time)
        
        return violations
        
    def enforce_post_call(
        self,
        function_id: str,
        return_value: Any,
        args: Dict[str, Any] = None
    ) -> List[EnforcementViolation]:
        """
        Enforce post-call constraints.
        
        Args:
            function_id: Function that was called
            return_value: Return value from function
            args: Original arguments (for cross-parameter checks)
            
        Returns:
            List of violations
        """
        violations = []
        
        if self.mode == EnforcementMode.DISABLED:
            return violations
            
        start_time = time.perf_counter_ns()
        
        # Get clauses for return value
        # Entity ID for return value is often function_id + ".return" 
        # or similar depending on the generation logic
        return_id = f"{function_id}.return"
        return_clauses = self.clause_index.get(return_id, [])
        
        for clause in return_clauses:
            violation = self._enforce_clause(clause, return_value, args or {})
            if violation:
                violations.append(violation)
                self.stats.record_violation(violation)
                self.adapter.report_violation(violation)
                
        end_time = time.perf_counter_ns()
        self.stats.record_enforcement_time(end_time - start_time)
        
        return violations
        
    def _enforce_clause(
        self,
        clause: ContractClause,
        value: Any,
        context: Dict[str, Any]
    ) -> Optional[EnforcementViolation]:
        """
        Enforce single clause.
        
        Args:
            clause: Clause to enforce
            value: Value to check
            context: Full context (args etc.)
            
        Returns:
            Violation if constraint not satisfied, None otherwise
        """
        # Skip if mode doesn't enforce this severity
        if self.mode == EnforcementMode.PRODUCTION:
            if clause.severity != Severity.FATAL and clause.severity != Severity.ERROR:
                return None
        
        # Enforce based on clause type
        if clause.clause_type == ClauseType.NULLABILITY:
            return self._enforce_nullability(clause, value, context)
            
        elif clause.clause_type == ClauseType.SIZE:
            return self._enforce_size(clause, value, context)
            
        elif clause.clause_type == ClauseType.ALIGNMENT:
            return self._enforce_alignment(clause, value, context)
            
        return None
        
    def _enforce_nullability(
        self,
        clause: ContractClause,
        value: Any,
        context: Dict[str, Any]
    ) -> Optional[EnforcementViolation]:
        """Enforce nullability clause."""
        nullable_param = clause.get_parameter("nullable")
        nullable = nullable_param.value if nullable_param else False
        
        if not self.adapter.check_nullability(value, nullable):
            return EnforcementViolation(
                clause_id=clause.clause_id,
                violation_type=ViolationType.NULLABILITY,
                entity_id=clause.subject_reference.entity_id,
                expected=f"nullable={nullable}",
                actual="None" if value is None else "not-None",
                severity=clause.severity,
                call_context=context
            )
        return None
        
    def _enforce_size(
        self,
        clause: ContractClause,
        value: Any,
        context: Dict[str, Any]
    ) -> Optional[EnforcementViolation]:
        """Enforce size clause."""
        size_param = clause.get_parameter("size_value")
        if not size_param:
            return None
            
        required_size = size_param.value
        
        if not self.adapter.check_size(value, required_size):
            actual_size = len(value) if hasattr(value, '__len__') else "unknown"
            return EnforcementViolation(
                clause_id=clause.clause_id,
                violation_type=ViolationType.SIZE,
                entity_id=clause.subject_reference.entity_id,
                expected=f"size >= {required_size}",
                actual=f"size={actual_size}",
                severity=clause.severity,
                call_context=context
            )
        return None
        
    def _enforce_alignment(
        self,
        clause: ContractClause,
        value: Any,
        context: Dict[str, Any]
    ) -> Optional[EnforcementViolation]:
        """Enforce alignment clause."""
        align_param = clause.get_parameter("required_alignment")
        if not align_param:
            return None
            
        required_alignment = align_param.value
        
        if not self.adapter.check_alignment(value, required_alignment):
            return EnforcementViolation(
                clause_id=clause.clause_id,
                violation_type=ViolationType.ALIGNMENT,
                entity_id=clause.subject_reference.entity_id,
                expected=f"alignment={required_alignment}",
                actual="misaligned",
                severity=clause.severity,
                call_context=context
            )
        return None

__all__ = [
    'EnforcementMode',
    'ViolationType',
    'EnforcementViolation',
    'EnforcementStats',
    'LanguageAdapter',
    'PythonAdapter',
    'EnforcementEngine',
]
