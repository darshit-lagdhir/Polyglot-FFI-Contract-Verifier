"""
Module 08: Language Adapter - Runtime FFI Enforcement System
============================================================

The Language Adapter transforms static contract artifacts into runtime-enforced
FFI boundaries. It interposes between foreign language runtimes and native code,
validating every cross-language invocation against explicit contract clauses.

This file contains the foundational architecture:
- Core enumerations
- ValidationNode & ValidationGraph
- OwnershipState & OwnershipRegistry
- EnforcementContext & ViolationReport
- ContractProjector
- LanguageAdapter main class
"""
from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

__version__ = '0.1.0'


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1: CORE ENUMERATIONS
# ════════════════════════════════════════════════════════════════════════════

class ClauseSeverity(Enum):
    """
    Severity classification for contract clauses.
    
    - MANDATORY: Must be satisfied; violation blocks execution
    - ADVISORY: Should be satisfied; violation logs warning
    - OPTIONAL: Nice to have; violation may be ignored
    """
    MANDATORY = "mandatory"
    ADVISORY = "advisory"
    OPTIONAL = "optional"


class OwnershipKind(Enum):
    """
    Ownership classification for pointers.
    
    - CALLER_OWNED: Caller allocated and must free
    - CALLEE_OWNED: Callee allocated and will free
    - SHARED: Ownership shared between caller and callee
    - TRANSFERRED: Ownership transferred during call
    - FREED: Pointer has been freed
    - UNKNOWN: Ownership status unknown
    """
    CALLER_OWNED = "caller_owned"
    CALLEE_OWNED = "callee_owned"
    SHARED = "shared"
    TRANSFERRED = "transferred"
    FREED = "freed"
    UNKNOWN = "unknown"


class ValidationStatus(Enum):
    """
    Validation result status.
    
    - PASS: Validation succeeded
    - FAIL: Validation failed
    - SKIPPED: Validation skipped (predicate not set)
    - ERROR: Validation encountered error
    """
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"


class EnforcementMode(Enum):
    """
    Global enforcement mode.
    
    - STRICT: All clauses treated as mandatory
    - ADVISORY: Advisory clauses log warnings only
    - PERMISSIVE: Continue execution on non-critical failures
    """
    STRICT = "strict"
    ADVISORY = "advisory"
    PERMISSIVE = "permissive"


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2: VALIDATION NODE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationNode:
    """
    Represents a single validation check in the enforcement graph.
    
    A ValidationNode encodes one contract clause as an executable predicate.
    It references parameters by index, contains the validation logic, and
    produces structured failure messages.
    
    Attributes:
        clause_id: Unique identifier for this clause
        clause_type: Type of validation (e.g., 'range', 'nullability')
        severity: Severity level (mandatory/advisory/optional)
        predicate: Optional validation function
        parameters: Indices of parameters this clause validates
        failure_message: Message template for validation failures
        metadata: Additional clause metadata
    """
    
    clause_id: str
    clause_type: str
    severity: ClauseSeverity
    predicate: Optional[Callable[[List[Any], List[int]], bool]] = None
    parameters: List[int] = field(default_factory=list)
    failure_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        """Make ValidationNode hashable for graph operations."""
        return hash((self.clause_id, self.clause_type))
    
    def __eq__(self, other: object) -> bool:
        """Equality based on clause_id and clause_type."""
        if not isinstance(other, ValidationNode):
            return False
        return (self.clause_id == other.clause_id and 
                self.clause_type == other.clause_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary containing all node attributes except predicate
        """
        return {
            'clause_id': self.clause_id,
            'clause_type': self.clause_type,
            'severity': self.severity.value,
            'parameters': self.parameters,
            'failure_message': self.failure_message,
            'metadata': self.metadata
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3: VALIDATION GRAPH
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationGraph:
    """
    Directed acyclic graph of validation nodes with dependency edges.
    
    Ensures relational validators execute only after individual parameter
    validators succeed. Supports topological traversal for deterministic
    execution order.
    
    Attributes:
        function_name: Name of function this graph validates
        nodes: List of validation nodes
        edges: Adjacency list representing dependencies
    """
    
    function_name: str
    nodes: List[ValidationNode] = field(default_factory=list)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_node(self, node: ValidationNode) -> None:
        """
        Add validation node to graph.
        
        Args:
            node: ValidationNode to add
        """
        if node not in self.nodes:
            self.nodes.append(node)
            if node.clause_id not in self.edges:
                self.edges[node.clause_id] = []
    
    def add_edge(self, from_clause: str, to_clause: str) -> None:
        """
        Add dependency edge (from_clause must execute before to_clause).
        
        Args:
            from_clause: Source clause ID
            to_clause: Target clause ID
        """
        if from_clause not in self.edges:
            self.edges[from_clause] = []
        if to_clause not in self.edges[from_clause]:
            self.edges[from_clause].append(to_clause)
    
    def get_execution_order(self) -> List[ValidationNode]:
        """
        Compute topological ordering of nodes for execution.
        """
        # Initialize in-degree for all nodes
        in_degree = {node.clause_id: 0 for node in self.nodes}
        
        # Calculate in-degrees
        for deps in self.edges.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Find all nodes with in-degree 0 (no dependencies)
        queue = [node for node in self.nodes if in_degree[node.clause_id] == 0]
        result = []
        
        # Kahn's algorithm
        while queue:
            # Pop node with no dependencies
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree of dependent nodes
            for dep_id in self.edges.get(node.clause_id, []):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        # Find node with this clause_id
                        dep_node = next(
                            n for n in self.nodes 
                            if n.clause_id == dep_id
                        )
                        queue.append(dep_node)
        
        # If result doesn't contain all nodes, there's a cycle
        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in validation graph")
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        """
        return {
            'function_name': self.function_name,
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': self.edges
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4: OWNERSHIP STATE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class OwnershipState:
    """
    Ownership state for a specific memory address.
    
    Tracks allocation origin, current owner, transfer history, and free
    eligibility. Used by ownership registry to enforce transfer semantics.
    """
    
    address: int
    kind: OwnershipKind
    allocated_at: str
    allocated_by: str
    transfer_history: List[Dict[str, Any]] = field(default_factory=list)
    free_eligible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def transfer_to(self, new_owner: str, timestamp: str) -> None:
        """
        Record ownership transfer.
        """
        if self.kind == OwnershipKind.FREED:
            raise ValueError(
                f"Cannot transfer freed pointer: {hex(self.address)}"
            )
        
        # Record transfer in history
        self.transfer_history.append({
            'from': self.allocated_by,
            'to': new_owner,
            'timestamp': timestamp,
            'previous_kind': self.kind.value
        })
        
        # Update current owner
        self.allocated_by = new_owner
    
    def mark_freed(self, timestamp: str) -> None:
        """
        Mark pointer as freed.
        """
        if self.kind == OwnershipKind.FREED:
            raise ValueError(
                f"Double-free detected: {hex(self.address)}"
            )
        
        if not self.free_eligible:
            raise ValueError(
                f"Pointer {hex(self.address)} not eligible for free"
            )
        
        # Update state
        self.kind = OwnershipKind.FREED
        self.free_eligible = False
        
        # Record in history
        self.transfer_history.append({
            'event': 'freed',
            'timestamp': timestamp
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        """
        return {
            'address': hex(self.address),
            'kind': self.kind.value,
            'allocated_at': self.allocated_at,
            'allocated_by': self.allocated_by,
            'transfer_history': self.transfer_history,
            'free_eligible': self.free_eligible,
            'metadata': self.metadata
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5: ENFORCEMENT CONTEXT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class EnforcementContext:
    """Per-invocation enforcement context."""
    
    function_name: str
    invocation_id: str
    normalized_inputs: List[Any] = field(default_factory=list)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    crashed: bool = False
    crash_info: Optional[Dict[str, Any]] = None
    ownership_deltas: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    def record_validation(
        self,
        clause_id: str,
        status: ValidationStatus,
        message: str = ""
    ) -> None:
        """Record validation result."""
        self.validation_results.append({
            'clause_id': clause_id,
            'status': status.value,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    def record_crash(self, exception: Exception, context: Dict[str, Any]) -> None:
        """Record native crash."""
        self.crashed = True
        self.crash_info = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'context': context,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def finalize(self) -> None:
        """Mark context as finalized with end timestamp."""
        self.end_time = datetime.utcnow().isoformat() + 'Z'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'function_name': self.function_name,
            'invocation_id': self.invocation_id,
            'validation_results': self.validation_results,
            'crashed': self.crashed,
            'crash_info': self.crash_info,
            'ownership_deltas': self.ownership_deltas,
            'start_time': self.start_time,
            'end_time': self.end_time
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6: VIOLATION REPORT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ViolationReport:
    """Structured diagnostic for contract violations."""
    
    function_name: str
    clause_id: str
    clause_type: str
    severity: ClauseSeverity
    expected: str
    observed: str
    message: str
    contract_fingerprint: str
    timestamp: str
    invocation_context: Dict[str, Any] = field(default_factory=dict)
    remediation_hints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'function_name': self.function_name,
            'clause_id': self.clause_id,
            'clause_type': self.clause_type,
            'severity': self.severity.value,
            'expected': self.expected,
            'observed': self.observed,
            'message': self.message,
            'contract_fingerprint': self.contract_fingerprint,
            'timestamp': self.timestamp,
            'invocation_context': self.invocation_context,
            'remediation_hints': self.remediation_hints
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7: CONTRACT PROJECTOR
# ════════════════════════════════════════════════════════════════════════════

class ContractProjector:
    """Projects contract artifacts into validation graphs."""
    
    def __init__(self):
        self.contract_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_contract(self, contract_path: Union[str, Path]) -> Dict[str, Any]:
        """Load contract artifact from file."""
        path = Path(contract_path)
        if not path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        
        self._validate_contract_structure(contract)
        fingerprint = self._compute_fingerprint(contract)
        self.contract_cache[fingerprint] = contract
        
        return contract
    
    def _validate_contract_structure(self, contract: Dict[str, Any]) -> None:
        """Validate contract has required fields."""
        required = ['schema_version', 'contract_id', 'functions']
        for field in required:
            if field not in contract:
                raise ValueError(f"Contract missing required field: {field}")
        
        schema_version = contract.get('schema_version')
        if not isinstance(schema_version, str):
            raise ValueError("schema_version must be string")
        
        major_version = schema_version.split('.')[0]
        if major_version != '1':
            raise ValueError(f"Unsupported schema version: {schema_version}")
    
    def _compute_fingerprint(self, contract: Dict[str, Any]) -> str:
        """Compute deterministic fingerprint."""
        contract_str = json.dumps(contract, sort_keys=True)
        return hashlib.sha256(contract_str.encode('utf-8')).hexdigest()
    
    def project_function(
        self,
        contract: Dict[str, Any],
        function_name: str
    ) -> ValidationGraph:
        """Project function's contract clauses into validation graph."""
        functions = contract.get('functions', {})
        if function_name not in functions:
            raise ValueError(f"Function not found: {function_name}")
        
        func_contract = functions[function_name]
        graph = ValidationGraph(function_name=function_name)
        
        # Project parameter clauses
        for param_idx, param in enumerate(func_contract.get('parameters', [])):
            param_name = param.get('name', f'param_{param_idx}')
            for clause in param.get('clauses', []):
                node = self._create_node(clause, param_idx, param_name)
                graph.add_node(node)
        
        return graph
    
    def _create_node(
        self,
        clause: Dict[str, Any],
        param_idx: int,
        param_name: str
    ) -> ValidationNode:
        """Create validation node from clause."""
        clause_id = clause.get('clause_id', f'clause_{param_idx}')
        clause_type = clause.get('clause_type', 'unknown')
        severity_str = clause.get('severity', 'mandatory')
        
        try:
            severity = ClauseSeverity(severity_str)
        except ValueError:
            severity = ClauseSeverity.MANDATORY
        
        return ValidationNode(
            clause_id=clause_id,
            clause_type=clause_type,
            severity=severity,
            parameters=[param_idx],
            failure_message=clause.get('failure_message', ''),
            metadata=clause.get('metadata', {})
        )


# ════════════════════════════════════════════════════════════════════════════
# SECTION 8: OWNERSHIP REGISTRY
# ════════════════════════════════════════════════════════════════════════════

class OwnershipRegistry:
    """Tracks pointer ownership across FFI boundaries."""
    
    def __init__(self):
        self.registry: Dict[int, OwnershipState] = {}
        self.allocation_counter = 0
    
    def register_allocation(
        self,
        address: int,
        kind: OwnershipKind,
        owner: str
    ) -> OwnershipState:
        """Register new allocation."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        state = OwnershipState(
            address=address,
            kind=kind,
            allocated_at=timestamp,
            allocated_by=owner
        )
        self.registry[address] = state
        self.allocation_counter += 1
        return state
    
    def get_state(self, address: int) -> Optional[OwnershipState]:
        """Get ownership state for address."""
        return self.registry.get(address)
    
    def transfer_ownership(
        self,
        address: int,
        new_owner: str,
        new_kind: OwnershipKind
    ) -> None:
        """Transfer ownership of pointer."""
        state = self.registry.get(address)
        if not state:
            raise ValueError(f"Pointer not registered: {hex(address)}")
        
        if state.kind == OwnershipKind.FREED:
            raise ValueError(f"Cannot transfer freed pointer: {hex(address)}")
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        state.transfer_to(new_owner, timestamp)
        state.kind = new_kind
    
    def mark_freed(self, address: int) -> None:
        """Mark pointer as freed."""
        state = self.registry.get(address)
        if not state:
            raise ValueError(f"Pointer not registered: {hex(address)}")
        
        if state.kind == OwnershipKind.FREED:
            raise ValueError(f"Double-free detected: {hex(address)}")
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        state.mark_freed(timestamp)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            'total_allocations': self.allocation_counter,
            'active_pointers': len([
                s for s in self.registry.values()
                if s.kind != OwnershipKind.FREED
            ]),
            'freed_pointers': len([
                s for s in self.registry.values()
                if s.kind == OwnershipKind.FREED
            ])
        }
        return stats
    
    def clear(self) -> None:
        """Clear all ownership records."""
        self.registry.clear()
        self.allocation_counter = 0


# ════════════════════════════════════════════════════════════════════════════
# SECTION 9: ADAPTER CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class AdapterConfig:
    """Adapter configuration."""
    
    mode: EnforcementMode = EnforcementMode.STRICT
    fail_fast: bool = True
    enable_crash_isolation: bool = True
    enable_ownership_tracking: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'mode': self.mode.value,
            'fail_fast': self.fail_fast,
            'enable_crash_isolation': self.enable_crash_isolation,
            'enable_ownership_tracking': self.enable_ownership_tracking
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 11: PREDICATE FACTORY
# ════════════════════════════════════════════════════════════════════════════

class PredicateFactory:
    """
    Factory for creating validation predicates from clause metadata.
    
    Generates callable predicate functions dynamically based on clause types
    and metadata, enabling contract-driven validation without manual coding.
    """
    
    @staticmethod
    def create_range_predicate(
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create numeric range validation predicate.
        
        Args:
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            
        Returns:
            Predicate function validating numeric range
        """
        def predicate(inputs: List[Any], param_indices: List[int]) -> bool:
            if not param_indices:
                return True
            
            value = inputs[param_indices[0]]
            
            # Handle None/null
            if value is None:
                return False
            
            # Convert to numeric
            try:
                num_value = float(value)
            except (TypeError, ValueError):
                return False
            
            # Check bounds
            if min_value is not None and num_value < min_value:
                return False
            if max_value is not None and num_value > max_value:
                return False
            
            return True
        
        return predicate
    
    @staticmethod
    def create_nullability_predicate(
        allow_null: bool = False
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create pointer nullability validation predicate.
        
        Args:
            allow_null: Whether null pointers are allowed
            
        Returns:
            Predicate function validating nullability
        """
        def predicate(inputs: List[Any], param_indices: List[int]) -> bool:
            if not param_indices:
                return True
            
            value = inputs[param_indices[0]]
            
            if allow_null:
                return True  # Null allowed
            else:
                return value is not None  # Null not allowed
        
        return predicate
    
    @staticmethod
    def create_type_predicate(
        expected_type: type
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create type validation predicate.
        
        Args:
            expected_type: Expected Python type
            
        Returns:
            Predicate function validating type
        """
        def predicate(inputs: List[Any], param_indices: List[int]) -> bool:
            if not param_indices:
                return True
            
            value = inputs[param_indices[0]]
            return isinstance(value, expected_type)
        
        return predicate
    
    @staticmethod
    def create_string_length_predicate(
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create string length validation predicate.
        
        Args:
            min_length: Minimum string length
            max_length: Maximum string length
            
        Returns:
            Predicate function validating string length
        """
        def predicate(inputs: List[Any], param_indices: List[int]) -> bool:
            if not param_indices:
                return True
            
            value = inputs[param_indices[0]]
            
            if not isinstance(value, str):
                return False
            
            length = len(value)
            
            if min_length is not None and length < min_length:
                return False
            if max_length is not None and length > max_length:
                return False
            
            return True
        
        return predicate
    
    @staticmethod
    def create_buffer_length_predicate(
        size_param_index: int
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create buffer-length relational predicate.
        
        Validates that buffer length matches size parameter.
        
        Args:
            size_param_index: Index of size parameter
            
        Returns:
            Predicate function validating buffer-size relationship
        """
        def predicate(inputs: List[Any], param_indices: List[int]) -> bool:
            if len(param_indices) < 1:
                return True
            
            buffer_idx = param_indices[0]
            
            if buffer_idx >= len(inputs) or size_param_index >= len(inputs):
                return False
            
            buffer = inputs[buffer_idx]
            size = inputs[size_param_index]
            
            # Handle None buffer with zero size
            if buffer is None and size == 0:
                return True
            
            if buffer is None:
                return False
            
            # Check buffer has required length
            try:
                buffer_len = len(buffer)
                return buffer_len >= size
            except TypeError:
                return False
        
        return predicate

    @staticmethod
    def create_compound_predicate(
        operator: str,
        sub_predicates: List[Callable]
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create compound predicate from sub-predicates.
        
        Args:
            operator: Logical operator ('and', 'or', 'not')
            sub_predicates: List of predicate functions
            
        Returns:
            Compound predicate function
        """
        compound = CompoundPredicate(operator, sub_predicates)
        return compound.__call__

    @staticmethod
    def create_conditional_predicate(
        condition_expr: str,
        then_predicate: Callable,
        else_predicate: Optional[Callable] = None
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create conditional predicate from expression.
        
        Args:
            condition_expr: Condition expression string
            then_predicate: Predicate if condition true
            else_predicate: Predicate if condition false
            
        Returns:
            Conditional predicate function
        """
        condition_pred = ExpressionPredicate(condition_expr)
        
        def condition_func(inputs: List[Any], params: List[int]) -> bool:
            return condition_pred(inputs, params)
            
        conditional = ConditionalPredicate(
            condition_func,
            then_predicate,
            else_predicate
        )
        return conditional.__call__

    @staticmethod
    def create_expression_predicate(
        expression: str
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create expression-based predicate.
        
        Args:
            expression: Python expression to evaluate
            
        Returns:
            Expression predicate function
        """
        pred = ExpressionPredicate(expression)
        return pred.__call__

    @staticmethod
    def create_alignment_predicate(
        alignment: int
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create alignment validation predicate.
        
        Args:
            alignment: Required alignment in bytes
            
        Returns:
            Alignment predicate function
        """
        pred = AlignmentPredicate(alignment)
        return pred.__call__

    @staticmethod
    def create_enum_predicate(
        allowed_values: List[Any]
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create enum validation predicate.
        
        Args:
            allowed_values: List of allowed enum values
            
        Returns:
            Enum predicate function
        """
        pred = EnumPredicate(allowed_values)
        return pred.__call__

    @staticmethod
    def create_bitwise_predicate(
        required_set: int = 0,
        required_unset: int = 0
    ) -> Callable[[List[Any], List[int]], bool]:
        """
        Create bitwise validation predicate.
        
        Args:
            required_set: Bits that must be set
            required_unset: Bits that must be unset
            
        Returns:
            Bitwise predicate function
        """
        pred = BitwisePredicate(required_set, required_unset)
        return pred.__call__

    @staticmethod
    def create_from_metadata(metadata: Dict[str, Any]) -> Callable:
        """
        Create predicate from metadata dictionary.
        
        Enables contract-driven predicate generation.
        
        Args:
            metadata: Clause metadata containing type and parameters
            
        Returns:
            Predicate function
        """
        clause_type = metadata.get('type', 'unknown')
        
        if clause_type == 'range':
            return PredicateFactory.create_range_predicate(
                metadata.get('min'),
                metadata.get('max')
            )
        
        elif clause_type == 'nullability':
            return PredicateFactory.create_nullability_predicate(
                metadata.get('allow_null', False)
            )
        
        elif clause_type == 'type':
            type_name = metadata.get('expected_type', 'int')
            type_map = {
                'int': int,
                'str': str,
                'float': float,
                'bool': bool
            }
            return PredicateFactory.create_type_predicate(
                type_map.get(type_name, int)
            )
        
        elif clause_type == 'string_length':
            return PredicateFactory.create_string_length_predicate(
                metadata.get('min_length'),
                metadata.get('max_length')
            )
        
        elif clause_type == 'alignment':
            return PredicateFactory.create_alignment_predicate(
                metadata.get('alignment', 1)
            )
        
        elif clause_type == 'enum':
            return PredicateFactory.create_enum_predicate(
                metadata.get('allowed_values', [])
            )
        
        elif clause_type == 'bitwise':
            return PredicateFactory.create_bitwise_predicate(
                metadata.get('required_set', 0),
                metadata.get('required_unset', 0)
            )
        
        elif clause_type == 'expression':
            return PredicateFactory.create_expression_predicate(
                metadata.get('expression', 'True')
            )
        
        elif clause_type == 'compound':
            operator = metadata.get('operator', 'and')
            sub_clauses = metadata.get('sub_clauses', [])
            sub_predicates = [
                PredicateFactory.create_from_metadata(sc)
                for sc in sub_clauses
            ]
            return PredicateFactory.create_compound_predicate(
                operator,
                sub_predicates
            )
        
        # Default: always pass
        return lambda inputs, params: True


# ════════════════════════════════════════════════════════════════════════════
# SECTION 12: VALIDATION ENGINE
# ════════════════════════════════════════════════════════════════════════════

class ValidationEngine:
    """
    Executes validation graphs against runtime values.
    
    Traverses validation graphs in topological order, evaluates predicates,
    and collects results. Supports fail-fast and aggregate violation modes.
    """
    
    def __init__(self):
        self.violation_handlers: List[Callable] = []
        self.predicate_factory = PredicateFactory()
    
    def register_violation_handler(self, handler: Callable) -> None:
        """
        Register violation callback.
        
        Args:
            handler: Callable receiving (node, inputs) on violation
        """
        self.violation_handlers.append(handler)
    
    def validate(
        self,
        graph: ValidationGraph,
        inputs: List[Any],
        context: EnforcementContext
    ) -> bool:
        """
        Execute validation graph.
        
        Args:
            graph: Validation graph to execute
            inputs: Normalized input values
            context: Enforcement context for recording results
            
        Returns:
            True if all validations pass, False otherwise
        """
        execution_order = graph.get_execution_order()
        
        for node in execution_order:
            # Skip if predicate not set
            if node.predicate is None:
                context.record_validation(
                    node.clause_id,
                    ValidationStatus.SKIPPED,
                    "Predicate not implemented"
                )
                continue
            
            # Execute predicate
            start_time = datetime.utcnow()
            
            try:
                result = node.predicate(inputs, node.parameters)
                
                # Calculate elapsed time in ms
                # (Not recorded in this basic validate method, but variable assigned)
                exec_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if result:
                    context.record_validation(
                        node.clause_id,
                        ValidationStatus.PASS
                    )
                else:
                    context.record_validation(
                        node.clause_id,
                        ValidationStatus.FAIL,
                        node.failure_message
                    )
                    
                    # Notify handlers
                    for handler in self.violation_handlers:
                        handler(node, inputs)
                    
                    # Fail fast for mandatory clauses
                    if node.severity == ClauseSeverity.MANDATORY:
                        return False
                
            except Exception as e:
                context.record_validation(
                    node.clause_id,
                    ValidationStatus.ERROR,
                    f"Predicate exception: {e}"
                )
                return False
        
        return True
    
    def validate_with_metrics(
        self,
        graph: ValidationGraph,
        inputs: List[Any],
        context: EnforcementContext
    ) -> Dict[str, Any]:
        """
        Execute validation with detailed metrics.
        
        Returns:
            Dictionary with validation result and performance metrics
        """
        start_time = datetime.utcnow()
        
        result = self.validate(graph, inputs, context)
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            'valid': result,
            'duration_ms': duration_ms,
            'total_validations': len(graph.nodes),
            'validations_passed': len([
                r for r in context.validation_results
                if r['status'] == 'pass'
            ]),
            'validations_failed': len([
                r for r in context.validation_results
                if r['status'] == 'fail'
            ])
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 10: LANGUAGE ADAPTER
# ════════════════════════════════════════════════════════════════════════════

class LanguageAdapter:
    """Main Language Adapter interface."""
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self.projector = ContractProjector()
        self.ownership_registry = OwnershipRegistry()
        self.validation_engine = ValidationEngine()
        self.orchestrator = InvocationOrchestrator(
            self.validation_engine,
            self.ownership_registry
        )
        self.contract_fingerprint: Optional[str] = None
        self.validation_graphs: Dict[str, ValidationGraph] = {}
    
    def load_contract(self, contract_path: Union[str, Path]) -> None:
        """Load contract artifact."""
        contract = self.projector.load_contract(contract_path)
        self.contract_fingerprint = self.projector._compute_fingerprint(contract)
        
        for func_name in contract.get('functions', {}).keys():
            graph = self.projector.project_function(contract, func_name)
            self.validation_graphs[func_name] = graph
    
    def get_validation_graph(self, function_name: str) -> Optional[ValidationGraph]:
        """Get validation graph for function."""
        return self.validation_graphs.get(function_name)
    
    def create_enforcement_context(self, function_name: str) -> EnforcementContext:
        """Create new enforcement context for invocation."""
        return EnforcementContext(
            function_name=function_name,
            invocation_id=str(uuid.uuid4()),
            start_time=datetime.utcnow().isoformat() + 'Z'
        )
    
    def validate_invocation(
        self,
        function_name: str,
        inputs: List[Any],
        context: Optional[EnforcementContext] = None
    ) -> Dict[str, Any]:
        """
        Validate function invocation against contract.
        
        Args:
            function_name: Name of function
            inputs: Normalized input values
            context: Optional enforcement context (created if not provided)
            
        Returns:
            Validation result dictionary
        """
        if context is None:
            context = self.create_enforcement_context(function_name)
        
        graph = self.get_validation_graph(function_name)
        if not graph:
            raise ValueError(f"No validation graph for function: {function_name}")
        
        context.normalized_inputs = inputs
        result = self.validation_engine.validate_with_metrics(graph, inputs, context)
        
        # context.finalize() if implemented, or just update status
        
# ════════════════════════════════════════════════════════════════════════════
# SECTION 13: PHASE RESULT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PhaseResult:
    """
    Result from a single pipeline phase.
    
    Tracks success, timing, diagnostics, and violations for one phase
    of the enforcement pipeline.
    """
    
    phase_name: str
    success: bool
    duration_ms: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    violations: List[ViolationReport] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'phase_name': self.phase_name,
            'success': self.success,
            'duration_ms': self.duration_ms,
            'diagnostics': self.diagnostics,
            'violations': [v.to_dict() for v in self.violations]
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 14: PIPELINE CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """
    Pipeline execution configuration.
    
    Controls pipeline behavior including phase execution, error handling,
    and performance options.
    """
    
    enable_normalization: bool = True
    enable_pre_validation: bool = True
    enable_ownership_checks: bool = True
    enable_post_validation: bool = True
    enable_ownership_reconciliation: bool = True
    fail_fast: bool = True
    dry_run: bool = False  # Skip native invocation for testing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enable_normalization': self.enable_normalization,
            'enable_pre_validation': self.enable_pre_validation,
            'enable_ownership_checks': self.enable_ownership_checks,
            'enable_post_validation': self.enable_post_validation,
            'enable_ownership_reconciliation': self.enable_ownership_reconciliation,
            'fail_fast': self.fail_fast,
            'dry_run': self.dry_run
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 15: NORMALIZATION INTERFACE
# ════════════════════════════════════════════════════════════════════════════

class NormalizationInterface:
    """
    Abstract interface for value normalization.
    
    Language-specific adapters implement this interface to convert
    their runtime values into canonical validation forms.
    """
    
    def normalize_value(self, value: Any) -> Any:
        """
        Normalize single value.
        
        Args:
            value: Language-specific value
            
        Returns:
            Normalized canonical value
            
        Raises:
            ValueError: If value cannot be normalized
        """
        # Default implementation: pass-through
        return value
    
    def normalize_inputs(self, inputs: List[Any]) -> List[Any]:
        """
        Normalize list of input values.
        
        Args:
            inputs: List of language-specific values
            
        Returns:
            List of normalized values
        """
        return [self.normalize_value(v) for v in inputs]
    
    def can_normalize(self, value: Any) -> bool:
        """
        Check if value can be normalized.
        
        Args:
            value: Value to check
            
        Returns:
            True if normalization possible, False otherwise
        """
        try:
            self.normalize_value(value)
            return True
        except (ValueError, TypeError):
            return False


# ════════════════════════════════════════════════════════════════════════════
# SECTION 16: INVOCATION ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════

class InvocationOrchestrator:
    """
    Orchestrates complete enforcement pipeline.
    
    Coordinates normalization, validation, ownership checking, native
    invocation, and post-call reconciliation in strict phase order.
    """
    
    def __init__(
        self,
        validation_engine: ValidationEngine,
        ownership_registry: OwnershipRegistry,
        config: Optional[PipelineConfig] = None
    ):
        self.validation_engine = validation_engine
        self.ownership_registry = ownership_registry
        self.config = config or PipelineConfig()
        self.normalizer = NormalizationInterface()
        self.crash_boundary = CrashIsolationBoundary()
        self.exception_translator = ExceptionTranslator()
        self.post_call_validator = PostCallValidator()
        self.phase_results: List[PhaseResult] = []
    
    def execute_pipeline(
        self,
        function_name: str,
        validation_graph: ValidationGraph,
        inputs: List[Any],
        context: EnforcementContext
    ) -> Dict[str, Any]:
        """
        Execute complete enforcement pipeline.
        
        Args:
            function_name: Name of function being invoked
            validation_graph: Validation graph for function
            inputs: Raw input values
            context: Enforcement context
            
        Returns:
            Pipeline execution result
        """
        self.phase_results = []
        
        # Phase 1: Normalization
        if self.config.enable_normalization:
            norm_result = self._phase_normalization(inputs)
            self.phase_results.append(norm_result)
            
            if not norm_result.success and self.config.fail_fast:
                return self._assemble_failure_result(context)
            
            normalized_inputs = norm_result.diagnostics.get('normalized', inputs)
        else:
            normalized_inputs = inputs
        
        context.normalized_inputs = normalized_inputs
        
        # Phase 2: Pre-call validation
        if self.config.enable_pre_validation:
            pre_val_result = self._phase_pre_validation(
                validation_graph,
                normalized_inputs,
                context
            )
            self.phase_results.append(pre_val_result)
            
            if not pre_val_result.success and self.config.fail_fast:
                return self._assemble_failure_result(context)
        
        # Phase 3: Ownership preconditions
        if self.config.enable_ownership_checks:
            own_check_result = self._phase_ownership_check(normalized_inputs)
            self.phase_results.append(own_check_result)
            
            if not own_check_result.success and self.config.fail_fast:
                return self._assemble_failure_result(context)
        
        # Phase 4: Native invocation (simulated for now)
        if not self.config.dry_run:
            invoke_result = self._phase_native_invocation(
                function_name,
                normalized_inputs
            )
            self.phase_results.append(invoke_result)
            
            if not invoke_result.success:
                return self._assemble_failure_result(context)
            
            native_result = invoke_result.diagnostics.get('result')
        else:
            native_result = None
        
        # Phase 5: Post-call validation (placeholder for now)
        if self.config.enable_post_validation:
            post_val_result = self._phase_post_validation(native_result)
            self.phase_results.append(post_val_result)
        
        # Phase 6: Ownership reconciliation (placeholder)
        if self.config.enable_ownership_reconciliation:
            recon_result = self._phase_ownership_reconciliation()
            self.phase_results.append(recon_result)
        
        context.finalize()
        
        return self._assemble_success_result(context, native_result)
    
    def _phase_normalization(self, inputs: List[Any]) -> PhaseResult:
        """Execute normalization phase."""
        start = datetime.utcnow()
        
        try:
            normalized = self.normalizer.normalize_inputs(inputs)
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            return PhaseResult(
                phase_name='normalization',
                success=True,
                duration_ms=duration,
                diagnostics={
                    'original_count': len(inputs),
                    'normalized': normalized
                }
            )
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            return PhaseResult(
                phase_name='normalization',
                success=False,
                duration_ms=duration,
                diagnostics={'error': str(e)}
            )
    
    def _phase_pre_validation(
        self,
        graph: ValidationGraph,
        inputs: List[Any],
        context: EnforcementContext
    ) -> PhaseResult:
        """Execute pre-call validation phase."""
        start = datetime.utcnow()
        
        result = self.validation_engine.validate(graph, inputs, context)
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        violations = []
        for val_result in context.validation_results:
            if val_result['status'] == 'fail':
                # Create violation report (simplified)
                violations.append(ViolationReport(
                    function_name=context.function_name,
                    clause_id=val_result['clause_id'],
                    clause_type='unknown',
                    severity=ClauseSeverity.MANDATORY,
                    expected='validation pass',
                    observed='validation fail',
                    message=val_result.get('message', ''),
                    contract_fingerprint='',
                    timestamp=val_result['timestamp']
                ))
        
        return PhaseResult(
            phase_name='pre_validation',
            success=result,
            duration_ms=duration,
            diagnostics={
                'validations_executed': len(graph.nodes),
                'validations_passed': len([
                    r for r in context.validation_results
                    if r['status'] == 'pass'
                ])
            },
            violations=violations
        )
    
    def _phase_ownership_check(self, inputs: List[Any]) -> PhaseResult:
        """Execute ownership precondition check phase."""
        start = datetime.utcnow()
        
        # Placeholder: Check if pointer inputs are registered
        # Real implementation in future prompts
        
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        return PhaseResult(
            phase_name='ownership_check',
            success=True,
            duration_ms=duration,
            diagnostics={'checked_count': 0}
        )
    
    def _phase_native_invocation(
        self,
        function_name: str,
        inputs: List[Any],
        native_callable: Optional[Callable] = None
    ) -> PhaseResult:
        """Execute native invocation with crash isolation."""
        start = datetime.utcnow()
        
        if native_callable is None:
            # Simulated invocation for testing
            native_callable = lambda *args: {'simulated': True, 'function': function_name}
        
        # Execute with crash isolation
        success, result, crash_ctx = self.crash_boundary.execute_isolated(
            native_callable,
            *inputs
        )
        
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        if success:
            return PhaseResult(
                phase_name='native_invocation',
                success=True,
                duration_ms=duration,
                diagnostics={'result': result}
            )
        else:
            # Crash occurred
            crash_ctx.function_name = function_name
            crash_ctx.normalized_inputs = inputs
            
            hints = self.exception_translator.extract_remediation_hints(crash_ctx)
            
            return PhaseResult(
                phase_name='native_invocation',
                success=False,
                duration_ms=duration,
                diagnostics={
                    'crash_context': crash_ctx.to_dict(),
                    'remediation_hints': hints,
                    'recoverable': self.crash_boundary.is_crash_recoverable(crash_ctx)
                }
            )
    
    def _phase_post_validation_enhanced(
        self,
        return_value: Any,
        output_params: Dict[int, Any],
        return_constraint: Optional[ReturnValueConstraint] = None,
        output_constraints: Optional[List[OutputParameterConstraint]] = None
    ) -> PhaseResult:
        """Execute enhanced post-call validation phase."""
        start = datetime.utcnow()
        
        validation_result = self.post_call_validator.validate_post_call(
            return_value,
            output_params,
            return_constraint,
            output_constraints
        )
        
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        return PhaseResult(
            phase_name='post_validation',
            success=validation_result['valid'],
            duration_ms=duration,
            diagnostics={
                'return_valid': validation_result['return_valid'],
                'outputs_valid': validation_result['outputs_valid'],
                'function_succeeded': validation_result['function_succeeded'],
                'violations_count': len(validation_result['violations']),
                'violations': validation_result['violations']
            }
        )
    
    def _phase_post_validation(self, result: Any) -> PhaseResult:
        """Execute post-call validation phase."""
        start = datetime.utcnow()
        
        # Placeholder: Validate return value
        # Real implementation in future prompts
        
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        return PhaseResult(
            phase_name='post_validation',
            success=True,
            duration_ms=duration,
            diagnostics={}
        )
    
    def _phase_ownership_reconciliation(self) -> PhaseResult:
        """Execute ownership reconciliation phase."""
        start = datetime.utcnow()
        
        # Placeholder: Update ownership registry
        # Real implementation in future prompts
        
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        return PhaseResult(
            phase_name='ownership_reconciliation',
            success=True,
            duration_ms=duration,
            diagnostics={}
        )
    
    def _assemble_success_result(
        self,
        context: EnforcementContext,
        native_result: Any
    ) -> Dict[str, Any]:
        """Assemble successful pipeline result."""
        return {
            'success': True,
            'result': native_result,
            'context': context.to_dict(),
            'phases': [p.to_dict() for p in self.phase_results],
            'total_duration_ms': sum(p.duration_ms for p in self.phase_results)
        }
    
    def _assemble_failure_result(
        self,
        context: EnforcementContext
    ) -> Dict[str, Any]:
        """Assemble failed pipeline result."""
        return {
            'success': False,
            'result': None,
            'context': context.to_dict(),
            'phases': [p.to_dict() for p in self.phase_results],
            'total_duration_ms': sum(p.duration_ms for p in self.phase_results),
            'failed_phase': next(
                (p.phase_name for p in self.phase_results if not p.success),
                None
            )
        }
    
    def get_phase_results(self) -> List[PhaseResult]:
        """Get all phase results from last execution."""
        return self.phase_results

    def invoke_with_enforcement(
        self,
        function_name: str,
        inputs: List[Any],
        pipeline_config: Optional[PipelineConfig] = None
    ) -> Dict[str, Any]:
        """
        Invoke function with full enforcement pipeline.
        
        Args:
            function_name: Name of function to invoke
            inputs: Raw input values
            pipeline_config: Optional pipeline configuration
            
        Returns:
            Pipeline execution result
        """
        graph = self.get_validation_graph(function_name)
        if not graph:
            raise ValueError(f"No validation graph for: {function_name}")
        
        context = self.create_enforcement_context(function_name)
        
        if pipeline_config:
            orchestrator = InvocationOrchestrator(
                self.validation_engine,
                self.ownership_registry,
                pipeline_config
            )
        else:
            orchestrator = self.orchestrator
        
        return orchestrator.execute_pipeline(
            function_name,
            graph,
            inputs,
            context
        )

    def invoke_with_enforcement_and_exceptions(
        self,
        function_name: str,
        inputs: List[Any],
        native_callable: Optional[Callable] = None
    ) -> Any:
        """
        Invoke function with enforcement and exception raising.
        
        Args:
            function_name: Function name
            inputs: Input values
            native_callable: Optional native function (for testing)
            
        Returns:
            Native function result
            
        Raises:
            ContractViolationException: If validation fails
            NativeCrashException: If native invocation crashes
        """
        result = self.invoke_with_enforcement(function_name, inputs)
        
        if not result['success']:
            # Check if crash or violation
            failed_phase = result.get('failed_phase')
            
            if failed_phase == 'native_invocation':
                # Native crash
                phases = result['phases']
                native_phase = next(
                    (p for p in phases if p['phase_name'] == 'native_invocation'),
                    None
                )
                
                if native_phase and 'crash_context' in native_phase['diagnostics']:
                    crash_dict = native_phase['diagnostics']['crash_context']
                    crash_ctx = CrashContext(
                        exception_type=crash_dict['exception_type'],
                        exception_message=crash_dict.get('exception_message', ''),
                        function_name=crash_dict['function_name']
                    )
                    
                    raise self.orchestrator.exception_translator.translate_crash(
                        crash_ctx,
                        EnforcementContext(function_name, result['context']['invocation_id'])
                    )
            
            # Contract violation
            phases = result['phases']
            for phase in phases:
                if phase['violations']:
                    violation_dict = phase['violations'][0]
                    violation = ViolationReport(
                        function_name=violation_dict['function_name'],
                        clause_id=violation_dict['clause_id'],
                        clause_type=violation_dict['clause_type'],
                        severity=ClauseSeverity(violation_dict['severity']),
                        expected=violation_dict['expected'],
                        observed=violation_dict['observed'],
                        message=violation_dict['message'],
                        contract_fingerprint=violation_dict['contract_fingerprint'],
                        timestamp=violation_dict['timestamp']
                    )
                    
                    raise self.orchestrator.exception_translator.translate_violation(violation)
        
        return result.get('result')

    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'config': self.config.to_dict(),
            'contract_fingerprint': self.contract_fingerprint,
            'loaded_functions': len(self.validation_graphs),
            'ownership': self.ownership_registry.get_statistics()
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 17: CRASH CONTEXT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class CrashContext:
    """
    Diagnostic information captured from native crash.
    
    Contains exception details, faulting address, function context,
    and other crash-specific diagnostics.
    """
    
    exception_type: str
    exception_code: Optional[int] = None
    exception_message: str = ""
    faulting_address: Optional[int] = None
    function_name: str = ""
    normalized_inputs: List[Any] = field(default_factory=list)
    stack_trace: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    platform: str = "unknown"
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'exception_type': self.exception_type,
            'exception_code': self.exception_code,
            'exception_message': self.exception_message,
            'faulting_address': hex(self.faulting_address) if self.faulting_address is not None else None,
            'function_name': self.function_name,
            'normalized_inputs_count': len(self.normalized_inputs),
            'stack_trace': self.stack_trace,
            'timestamp': self.timestamp,
            'platform': self.platform,
            'additional_info': self.additional_info
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 18: EXCEPTION TYPES
# ════════════════════════════════════════════════════════════════════════════

class ContractViolationException(Exception):
    """
    Exception raised when contract validation fails.
    
    Contains violation report and enforcement context for debugging.
    """
    
    def __init__(
        self,
        message: str,
        violation_report: ViolationReport,
        enforcement_context: Optional[EnforcementContext] = None
    ):
        super().__init__(message)
        self.violation_report = violation_report
        self.enforcement_context = enforcement_context
    
    def __str__(self) -> str:
        """String representation."""
        parts = [
            f"Contract Violation: {self.args[0]}",
            f"Function: {self.violation_report.function_name}",
            f"Clause: {self.violation_report.clause_id}",
            f"Expected: {self.violation_report.expected}",
            f"Observed: {self.violation_report.observed}"
        ]
        return '\n'.join(parts)


class NativeCrashException(Exception):
    """
    Exception raised when native invocation crashes.
    
    Contains crash context and diagnostic information.
    """
    
    def __init__(
        self,
        message: str,
        crash_context: CrashContext,
        enforcement_context: Optional[EnforcementContext] = None
    ):
        super().__init__(message)
        self.crash_context = crash_context
        self.enforcement_context = enforcement_context
    
    def __str__(self) -> str:
        """String representation."""
        parts = [
            f"Native Crash: {self.args[0]}",
            f"Exception Type: {self.crash_context.exception_type}",
            f"Function: {self.crash_context.function_name}",
        ]
        
        if self.crash_context.exception_code is not None:
            parts.append(f"Exception Code: 0x{self.crash_context.exception_code:08X}")
        
        if self.crash_context.faulting_address is not None:
            parts.append(f"Faulting Address: {hex(self.crash_context.faulting_address)}")
        
        return '\n'.join(parts)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 19: CRASH ISOLATION BOUNDARY
# ════════════════════════════════════════════════════════════════════════════

class CrashIsolationBoundary:
    """
    Platform-neutral crash isolation interface.
    
    Provides abstraction for capturing native crashes across platforms.
    Concrete implementations handle platform-specific details.
    """
    
    def __init__(self):
        self.enabled = True
        self.crash_handler_installed = False
    
    def install_crash_handler(self) -> bool:
        """
        Install platform-specific crash handler.
        
        Returns:
            True if handler installed successfully, False otherwise
        """
        # Platform-specific implementation in subclasses
        self.crash_handler_installed = True
        return True
    
    def uninstall_crash_handler(self) -> bool:
        """
        Uninstall crash handler.
        
        Returns:
            True if handler uninstalled successfully
        """
        self.crash_handler_installed = False
        return True
    
    def execute_isolated(
        self,
        callable_func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[CrashContext]]:
        """
        Execute callable with crash isolation.
        
        Args:
            callable_func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (success, result, crash_context)
            - success: True if no crash, False if crash occurred
            - result: Return value if successful, None if crash
            - crash_context: CrashContext if crash, None otherwise
        """
        if not self.enabled:
            # No isolation, direct call
            try:
                result = callable_func(*args, **kwargs)
                return (True, result, None)
            except Exception as e:
                crash_ctx = CrashContext(
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                    platform='python'
                )
                return (False, None, crash_ctx)
        
        # With isolation (simulated for base class)
        try:
            result = callable_func(*args, **kwargs)
            return (True, result, None)
        except Exception as e:
            # Convert to crash context
            crash_ctx = CrashContext(
                exception_type=type(e).__name__,
                exception_message=str(e),
                platform='python'
            )
            return (False, None, crash_ctx)
    
    def is_crash_recoverable(self, crash_context: CrashContext) -> bool:
        """
        Check if crash is recoverable.
        
        Some crashes (like assertion failures) may allow recovery,
        while others (like stack corruption) do not.
        
        Args:
            crash_context: Crash context to analyze
            
        Returns:
            True if recovery possible, False otherwise
        """
        # Most crashes are not recoverable
        unrecoverable = [
            'StackCorruption',
            'StackOverflow',
            'OutOfMemory'
        ]
        
        return crash_context.exception_type not in unrecoverable


# ════════════════════════════════════════════════════════════════════════════
# SECTION 20: EXCEPTION TRANSLATOR
# ════════════════════════════════════════════════════════════════════════════

class ExceptionTranslator:
    """
    Translates native crashes and contract violations into foreign exceptions.
    
    Converts crash contexts and violation reports into appropriate exception
    types for the foreign runtime.
    """
    
    def translate_crash(
        self,
        crash_context: CrashContext,
        enforcement_context: Optional[EnforcementContext] = None
    ) -> NativeCrashException:
        """
        Translate crash context to exception.
        
        Args:
            crash_context: Captured crash context
            enforcement_context: Optional enforcement context
            
        Returns:
            NativeCrashException instance
        """
        message = f"Native crash in {crash_context.function_name}: {crash_context.exception_message}"
        
        return NativeCrashException(
            message,
            crash_context,
            enforcement_context
        )
    
    def translate_violation(
        self,
        violation_report: ViolationReport,
        enforcement_context: Optional[EnforcementContext] = None
    ) -> ContractViolationException:
        """
        Translate violation report to exception.
        
        Args:
            violation_report: Violation report
            enforcement_context: Optional enforcement context
            
        Returns:
            ContractViolationException instance
        """
        message = f"Contract violation in {violation_report.function_name}: {violation_report.message}"
        
        return ContractViolationException(
            message,
            violation_report,
            enforcement_context
        )
    
    def extract_remediation_hints(
        self,
        crash_context: CrashContext
    ) -> List[str]:
        """
        Extract remediation hints from crash context.
        
        Args:
            crash_context: Crash context to analyze
            
        Returns:
            List of remediation hints
        """
        hints = []
        
        if crash_context.exception_type == 'NullPointerException':
            hints.append("Check that pointer parameters are not null")
            hints.append("Verify buffer allocation before passing to function")
        
        if crash_context.exception_type == 'AccessViolation':
            hints.append("Verify buffer size matches size parameter")
            hints.append("Check pointer validity and alignment")
        
        if crash_context.exception_type == 'StackOverflow':
            hints.append("Reduce recursion depth")
            hints.append("Check for infinite recursion")
        
        if crash_context.faulting_address == 0:
            hints.append("Null pointer dereference detected")
            hints.append("Ensure pointer is initialized before use")
        
        return hints


# ════════════════════════════════════════════════════════════════════════════
# SECTION 21: COMPOUND PREDICATES
# ════════════════════════════════════════════════════════════════════════════

class CompoundPredicate:
    """
    Combines multiple predicates with logical operators.
    
    Supports AND, OR, NOT composition for complex validation logic.
    """
    
    def __init__(
        self,
        operator: str,
        predicates: List[Callable[[List[Any], List[int]], bool]]
    ):
        """
        Initialize compound predicate.
        
        Args:
            operator: Logical operator ('and', 'or', 'not')
            predicates: List of predicate functions
        """
        self.operator = operator.lower()
        self.predicates = predicates
        
        if self.operator not in ['and', 'or', 'not']:
            raise ValueError(f"Invalid operator: {operator}")
        
        if self.operator == 'not' and len(predicates) != 1:
            raise ValueError("NOT operator requires exactly one predicate")
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute compound predicate."""
        if self.operator == 'and':
            return all(pred(inputs, param_indices) for pred in self.predicates)
        elif self.operator == 'or':
            return any(pred(inputs, param_indices) for pred in self.predicates)
        elif self.operator == 'not':
            return not self.predicates[0](inputs, param_indices)
        
        return False


# ════════════════════════════════════════════════════════════════════════════
# SECTION 22: CONDITIONAL PREDICATE
# ════════════════════════════════════════════════════════════════════════════

class ConditionalPredicate:
    """
    Executes predicate based on runtime condition.
    
    Enables context-dependent validation (e.g., validate buffer only if size > 0).
    """
    
    def __init__(
        self,
        condition: Callable[[List[Any], List[int]], bool],
        then_predicate: Callable[[List[Any], List[int]], bool],
        else_predicate: Optional[Callable[[List[Any], List[int]], bool]] = None
    ):
        """
        Initialize conditional predicate.
        
        Args:
            condition: Condition function
            then_predicate: Predicate to execute if condition true
            else_predicate: Predicate to execute if condition false
        """
        self.condition = condition
        self.then_predicate = then_predicate
        self.else_predicate = else_predicate or (lambda inputs, params: True)
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute conditional predicate."""
        if self.condition(inputs, param_indices):
            return self.then_predicate(inputs, param_indices)
        else:
            return self.else_predicate(inputs, param_indices)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 23: EXPRESSION PREDICATE
# ════════════════════════════════════════════════════════════════════════════

class ExpressionPredicate:
    """
    Evaluates custom expression for validation.
    
    Provides safe expression evaluation with restricted namespace.
    """
    
    def __init__(
        self,
        expression: str,
        allowed_names: Optional[Set[str]] = None
    ):
        """
        Initialize expression predicate.
        
        Args:
            expression: Python expression to evaluate
            allowed_names: Set of allowed variable names
        """
        self.expression = expression
        self.allowed_names = allowed_names or {'inputs', 'len', 'abs', 'min', 'max'}
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute expression predicate."""
        # Create safe namespace
        safe_globals = {
            '__builtins__': {},
            'inputs': inputs,
            'len': len,
            'abs': abs,
            'min': min,
            'max': max
        }
        
        # Validate expression doesn't use forbidden operations
        forbidden = ['import', 'exec', 'eval', '__', 'open', 'file']
        if any(word in self.expression.lower() for word in forbidden):
            raise ValueError(f"Expression contains forbidden operations")
        
        try:
            result = eval(self.expression, safe_globals, {})
            return bool(result)
        except Exception:
            return False


# ════════════════════════════════════════════════════════════════════════════
# SECTION 24: ALIGNMENT PREDICATE
# ════════════════════════════════════════════════════════════════════════════

class AlignmentPredicate:
    """
    Validates memory alignment requirements.
    
    Ensures pointer addresses meet alignment constraints (e.g., 4-byte, 8-byte).
    """
    
    def __init__(self, alignment: int):
        """
        Initialize alignment predicate.
        
        Args:
            alignment: Required alignment in bytes (must be power of 2)
        """
        if alignment <= 0 or (alignment & (alignment - 1)) != 0:
            raise ValueError(f"Alignment must be power of 2, got {alignment}")
        
        self.alignment = alignment
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute alignment predicate."""
        if not param_indices:
            return True
        
        value = inputs[param_indices[0]]
        
        # Handle integer addresses
        if isinstance(value, int):
            return (value % self.alignment) == 0
        
        # Cannot validate non-integer alignment
        return True


# ════════════════════════════════════════════════════════════════════════════
# SECTION 25: ENUM PREDICATE
# ════════════════════════════════════════════════════════════════════════════

class EnumPredicate:
    """
    Validates enum value membership.
    
    Ensures value is one of allowed enum values.
    """
    
    def __init__(self, allowed_values: List[Any]):
        """
        Initialize enum predicate.
        
        Args:
            allowed_values: List of allowed enum values
        """
        self.allowed_values = set(allowed_values)
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute enum predicate."""
        if not param_indices:
            return True
        
        value = inputs[param_indices[0]]
        return value in self.allowed_values


# ════════════════════════════════════════════════════════════════════════════
# SECTION 26: BITWISE PREDICATE
# ════════════════════════════════════════════════════════════════════════════

class BitwisePredicate:
    """
    Validates bitfield flags and masks.
    
    Checks that required bits are set/unset in bitfield values.
    """
    
    def __init__(
        self,
        required_set: int = 0,
        required_unset: int = 0
    ):
        """
        Initialize bitwise predicate.
        
        Args:
            required_set: Bitmask of bits that must be set
            required_unset: Bitmask of bits that must be unset
        """
        self.required_set = required_set
        self.required_unset = required_unset
    
    def __call__(
        self,
        inputs: List[Any],
        param_indices: List[int]
    ) -> bool:
        """Execute bitwise predicate."""
        if not param_indices:
            return True
        
        value = inputs[param_indices[0]]
        
        if not isinstance(value, int):
            return False
        
        # Check required set bits
        if (value & self.required_set) != self.required_set:
            return False
        
        # Check required unset bits
        if (value & self.required_unset) != 0:
            return False
        
        return True


# ════════════════════════════════════════════════════════════════════════════
# SECTION 27: PREDICATE REGISTRY
# ════════════════════════════════════════════════════════════════════════════

class PredicateRegistry:
    """
    Registry for named predicates.
    
    Allows predicates to be stored, retrieved, and reused by name.
    """
    
    def __init__(self):
        self.predicates: Dict[str, Callable] = {}
    
    def register(
        self,
        name: str,
        predicate: Callable[[List[Any], List[int]], bool]
    ) -> None:
        """
        Register named predicate.
        
        Args:
            name: Predicate name
            predicate: Predicate function
        """
        self.predicates[name] = predicate
    
    def get(self, name: str) -> Optional[Callable]:
        """
        Get predicate by name.
        
        Args:
            name: Predicate name
            
        Returns:
            Predicate function or None if not found
        """
        return self.predicates.get(name)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister predicate.
        
        Args:
            name: Predicate name
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self.predicates:
            del self.predicates[name]
            return True
        return False
    
    def list_predicates(self) -> List[str]:
        """Get list of registered predicate names."""
        return list(self.predicates.keys())

# ════════════════════════════════════════════════════════════════════════════
# SECTION 29: RETURN VALUE VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ReturnValueConstraint:
    """
    Constraints for return value validation.
    
    Defines expected type, range, nullability, and ownership for
    function return values.
    """
    
    expected_type: Optional[type] = None
    allow_null: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    ownership: Optional[OwnershipKind] = None
    alignment: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'expected_type': self.expected_type.__name__ if self.expected_type else None,
            'allow_null': self.allow_null,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'allowed_values': self.allowed_values,
            'ownership': self.ownership.value if self.ownership else None,
            'alignment': self.alignment
        }


class ReturnValueValidator:
    """
    Validates function return values against constraints.
    
    Checks type, range, nullability, and ownership of return values.
    """
    
    def __init__(self):
        self.predicate_factory = PredicateFactory()
    
    def validate(
        self,
        return_value: Any,
        constraint: ReturnValueConstraint
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate return value against constraint.
        
        Args:
            return_value: Returned value from function
            constraint: Return value constraint
            
        Returns:
            Tuple of (valid, error_message)
        """
        # Type validation
        if constraint.expected_type is not None:
            if not isinstance(return_value, constraint.expected_type):
                return (False, f"Expected type {constraint.expected_type.__name__}, got {type(return_value).__name__}")
        
        # Nullability validation
        if not constraint.allow_null and return_value is None:
            return (False, "Return value must not be null")
        
        # Skip further validation if null
        if return_value is None:
            return (True, None)
        
        # Range validation
        if constraint.min_value is not None or constraint.max_value is not None:
            try:
                num_value = float(return_value)
                if constraint.min_value is not None and num_value < constraint.min_value:
                    return (False, f"Return value {num_value} below minimum {constraint.min_value}")
                if constraint.max_value is not None and num_value > constraint.max_value:
                    return (False, f"Return value {num_value} above maximum {constraint.max_value}")
            except (TypeError, ValueError):
                return (False, f"Cannot validate range for non-numeric value")
        
        # Enum validation
        if constraint.allowed_values is not None:
            if return_value not in constraint.allowed_values:
                return (False, f"Return value {return_value} not in allowed values")
        
        # Alignment validation
        if constraint.alignment is not None:
            if isinstance(return_value, int):
                if (return_value % constraint.alignment) != 0:
                    return (False, f"Return value {hex(return_value)} not aligned to {constraint.alignment} bytes")
        
        return (True, None)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 30: OUTPUT PARAMETER VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class OutputParameterConstraint:
    """
    Constraints for output parameter validation.
    
    Defines requirements for parameters that callee writes to.
    """
    
    param_index: int
    required: bool = True  # Must be written to
    expected_type: Optional[type] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    max_bytes_written: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'param_index': self.param_index,
            'required': self.required,
            'expected_type': self.expected_type.__name__ if self.expected_type else None,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'max_bytes_written': self.max_bytes_written
        }


class OutputParameterValidator:
    """
    Validates output parameters after function returns.
    
    Checks that callee properly initialized output parameters.
    """
    
    def validate(
        self,
        param_value: Any,
        constraint: OutputParameterConstraint
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate output parameter.
        
        Args:
            param_value: Parameter value after call
            constraint: Output parameter constraint
            
        Returns:
            Tuple of (valid, error_message)
        """
        # Required check
        if constraint.required and param_value is None:
            return (False, f"Required output parameter {constraint.param_index} not initialized")
        
        if param_value is None:
            return (True, None)
        
        # Type validation
        if constraint.expected_type is not None:
            if not isinstance(param_value, constraint.expected_type):
                return (False, f"Output parameter type mismatch")
        
        # Range validation
        if constraint.min_value is not None or constraint.max_value is not None:
            try:
                num_value = float(param_value)
                if constraint.min_value is not None and num_value < constraint.min_value:
                    return (False, f"Output value {num_value} below minimum")
                if constraint.max_value is not None and num_value > constraint.max_value:
                    return (False, f"Output value {num_value} above maximum")
            except (TypeError, ValueError):
                pass
        
        return (True, None)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 31: ERROR CODE INTERPRETER
# ════════════════════════════════════════════════════════════════════════════

class ErrorCodeInterpreter:
    """
    Interprets function return values as error codes.
    
    Determines if function succeeded or failed based on return value.
    """
    
    def __init__(self):
        self.error_patterns: Dict[str, Callable[[Any], bool]] = {
            'negative_is_error': lambda val: isinstance(val, int) and val < 0,
            'zero_is_success': lambda val: val == 0,
            'null_is_error': lambda val: val is None,
            'false_is_error': lambda val: val is False
        }
    
    def register_pattern(
        self,
        name: str,
        pattern: Callable[[Any], bool]
    ) -> None:
        """
        Register custom error pattern.
        
        Args:
            name: Pattern name
            pattern: Function returning True if value indicates error
        """
        self.error_patterns[name] = pattern
    
    def is_error(
        self,
        return_value: Any,
        pattern_name: str = 'negative_is_error'
    ) -> bool:
        """
        Check if return value indicates error.
        
        Args:
            return_value: Return value to check
            pattern_name: Error pattern to use
            
        Returns:
            True if return value indicates error
        """
        pattern = self.error_patterns.get(pattern_name)
        if pattern is None:
            return False
        
        return pattern(return_value)
    
    def is_success(
        self,
        return_value: Any,
        pattern_name: str = 'zero_is_success'
    ) -> bool:
        """
        Check if return value indicates success.
        
        Args:
            return_value: Return value to check
            pattern_name: Success pattern to use
            
        Returns:
            True if return value indicates success
        """
        pattern = self.error_patterns.get(pattern_name)
        if pattern is None:
            return True
        
        return pattern(return_value)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 32: MEMORY INSPECTOR
# ════════════════════════════════════════════════════════════════════════════

class MemoryInspector:
    """
    Inspects memory regions for correctness.
    
    Provides basic memory inspection capabilities for output validation.
    """
    
    def __init__(self):
        self.snapshots: Dict[int, bytes] = {}
    
    def take_snapshot(
        self,
        address: int,
        size: int,
        data: Any
    ) -> str:
        """
        Take memory snapshot before call.
        
        Args:
            address: Memory address (identifier)
            size: Size in bytes
            data: Data to snapshot
            
        Returns:
            Snapshot identifier
        """
        snapshot_id = f"{address}_{size}"
        
        # Convert data to bytes for comparison
        if isinstance(data, bytes):
            self.snapshots[address] = data
        elif isinstance(data, (bytearray, memoryview)):
            self.snapshots[address] = bytes(data)
        
        return snapshot_id
    
    def compare_snapshot(
        self,
        address: int,
        current_data: Any
    ) -> Dict[str, Any]:
        """
        Compare current data with snapshot.
        
        Args:
            address: Memory address
            current_data: Current data
            
        Returns:
            Comparison result dictionary
        """
        if address not in self.snapshots:
            return {
                'has_snapshot': False,
                'modified': False
            }
        
        original = self.snapshots[address]
        
        # Convert current data
        if isinstance(current_data, bytes):
            current = current_data
        elif isinstance(current_data, (bytearray, memoryview)):
            current = bytes(current_data)
        else:
            return {'has_snapshot': True, 'modified': False}
        
        return {
            'has_snapshot': True,
            'modified': original != current,
            'bytes_changed': sum(1 for a, b in zip(original, current) if a != b)
        }
    
    def clear_snapshots(self) -> None:
        """Clear all snapshots."""
        self.snapshots.clear()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 33: POST-CALL VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

class PostCallValidator:
    """
    Orchestrates post-call validation.
    
    Coordinates return value validation, output parameter validation,
    and error code interpretation.
    """
    
    def __init__(self):
        self.return_validator = ReturnValueValidator()
        self.output_validator = OutputParameterValidator()
        self.error_interpreter = ErrorCodeInterpreter()
        self.memory_inspector = MemoryInspector()
    
    def validate_post_call(
        self,
        return_value: Any,
        output_params: Dict[int, Any],
        return_constraint: Optional[ReturnValueConstraint] = None,
        output_constraints: Optional[List[OutputParameterConstraint]] = None,
        error_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate post-call outputs.
        
        Args:
            return_value: Function return value
            output_params: Dictionary mapping param index to value
            return_constraint: Return value constraint
            output_constraints: List of output parameter constraints
            error_pattern: Error code pattern name
            
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': True,
            'return_valid': True,
            'outputs_valid': True,
            'function_succeeded': True,
            'violations': []
        }
        
        # Check for error
        if error_pattern:
            if self.error_interpreter.is_error(return_value, error_pattern):
                result['function_succeeded'] = False
                result['error_code'] = return_value
                # Skip output validation if function failed
                return result
        
        # Validate return value
        if return_constraint:
            valid, error_msg = self.return_validator.validate(
                return_value,
                return_constraint
            )
            result['return_valid'] = valid
            if not valid:
                result['valid'] = False
                result['violations'].append({
                    'type': 'return_value',
                    'message': error_msg
                })
        
        # Validate output parameters
        if output_constraints:
            for constraint in output_constraints:
                param_value = output_params.get(constraint.param_index)
                valid, error_msg = self.output_validator.validate(
                    param_value,
                    constraint
                )
                
                if not valid:
                    result['outputs_valid'] = False
                    result['valid'] = False
                    result['violations'].append({
                        'type': 'output_parameter',
                        'param_index': constraint.param_index,
                        'message': error_msg
                    })
        
        return result

# ════════════════════════════════════════════════════════════════════════════
# SECTION 34: ENFORCEMENT POLICY
# ════════════════════════════════════════════════════════════════════════════

class PolicyType(Enum):
    """Enforcement policy types."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"
    CUSTOM = "custom"


@dataclass
class EnforcementPolicy:
    """
    Defines enforcement behavior for contract violations.
    
    Controls how violations are handled, logged, and reported based
    on clause severity and policy configuration.
    """
    
    policy_type: PolicyType
    fail_fast: bool = True
    treat_advisory_as_mandatory: bool = False
    treat_optional_as_advisory: bool = True
    allow_missing_clauses: bool = False
    max_violations: int = 0  # 0 = unlimited
    violation_callback: Optional[Callable] = None
    
    @staticmethod
    def strict() -> 'EnforcementPolicy':
        """Create strict enforcement policy."""
        return EnforcementPolicy(
            policy_type=PolicyType.STRICT,
            fail_fast=True,
            treat_advisory_as_mandatory=True,
            treat_optional_as_advisory=True,
            allow_missing_clauses=False,
            max_violations=1
        )
    
    @staticmethod
    def balanced() -> 'EnforcementPolicy':
        """Create balanced enforcement policy."""
        return EnforcementPolicy(
            policy_type=PolicyType.BALANCED,
            fail_fast=False,
            treat_advisory_as_mandatory=False,
            treat_optional_as_advisory=True,
            allow_missing_clauses=True,
            max_violations=10
        )
    
    @staticmethod
    def permissive() -> 'EnforcementPolicy':
        """Create permissive enforcement policy."""
        return EnforcementPolicy(
            policy_type=PolicyType.PERMISSIVE,
            fail_fast=False,
            treat_advisory_as_mandatory=False,
            treat_optional_as_advisory=False,
            allow_missing_clauses=True,
            max_violations=0
        )
    
    def should_enforce(self, severity: ClauseSeverity) -> bool:
        """
        Determine if clause should be enforced.
        
        Args:
            severity: Clause severity
            
        Returns:
            True if clause should be enforced
        """
        if severity == ClauseSeverity.MANDATORY:
            return True
        
        if severity == ClauseSeverity.ADVISORY:
            return self.treat_advisory_as_mandatory
        
        if severity == ClauseSeverity.OPTIONAL:
            return self.treat_optional_as_advisory
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'policy_type': self.policy_type.value,
            'fail_fast': self.fail_fast,
            'treat_advisory_as_mandatory': self.treat_advisory_as_mandatory,
            'treat_optional_as_advisory': self.treat_optional_as_advisory,
            'allow_missing_clauses': self.allow_missing_clauses,
            'max_violations': self.max_violations
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 35: PERFORMANCE PROFILE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PerformanceProfile:
    """
    Performance tuning configuration.
    
    Controls optimization level, caching, and performance-related options.
    """
    
    optimization_level: int = 1  # 0-3
    enable_caching: bool = False
    parallel_validation: bool = False
    lazy_validation: bool = False
    clause_timeout_ms: int = 1000
    profile_execution: bool = False
    
    @staticmethod
    def fast() -> 'PerformanceProfile':
        """High-performance profile."""
        return PerformanceProfile(
            optimization_level=3,
            enable_caching=True,
            parallel_validation=True,
            lazy_validation=True,
            clause_timeout_ms=100,
            profile_execution=False
        )
    
    @staticmethod
    def balanced() -> 'PerformanceProfile':
        """Balanced performance profile."""
        return PerformanceProfile(
            optimization_level=1,
            enable_caching=False,
            parallel_validation=False,
            lazy_validation=False,
            clause_timeout_ms=1000,
            profile_execution=False
        )
    
    @staticmethod
    def debug() -> 'PerformanceProfile':
        """Debug-focused profile."""
        return PerformanceProfile(
            optimization_level=0,
            enable_caching=False,
            parallel_validation=False,
            lazy_validation=False,
            clause_timeout_ms=5000,
            profile_execution=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'optimization_level': self.optimization_level,
            'enable_caching': self.enable_caching,
            'parallel_validation': self.parallel_validation,
            'lazy_validation': self.lazy_validation,
            'clause_timeout_ms': self.clause_timeout_ms,
            'profile_execution': self.profile_execution
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 36: ADAPTER CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class AdapterConfiguration:
    """
    Complete adapter configuration.
    
    Combines enforcement policy, performance profile, pipeline config,
    and debugging options into unified configuration.
    """
    
    enforcement_policy: EnforcementPolicy = field(default_factory=EnforcementPolicy.balanced)
    performance_profile: PerformanceProfile = field(default_factory=PerformanceProfile.balanced)
    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)
    
    # Debugging options
    verbose_logging: bool = False
    trace_validation: bool = False
    dump_inputs: bool = False
    dump_memory: bool = False
    
    # Validation tuning
    ignore_clause_types: Set[str] = field(default_factory=set)
    require_clause_types: Set[str] = field(default_factory=set)
    
    # Function-specific overrides
    function_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_effective_config(
        self,
        function_name: Optional[str] = None
    ) -> 'AdapterConfiguration':
        """
        Get effective configuration with function overrides applied.
        
        Args:
            function_name: Function name for override lookup
            
        Returns:
            Configuration with overrides applied
        """
        if not function_name or function_name not in self.function_overrides:
            return self
        
        # Create copy with overrides
        import copy
        config = copy.deepcopy(self)
        overrides = self.function_overrides[function_name]
        
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enforcement_policy': self.enforcement_policy.to_dict(),
            'performance_profile': self.performance_profile.to_dict(),
            'pipeline_config': self.pipeline_config.to_dict(),
            'verbose_logging': self.verbose_logging,
            'trace_validation': self.trace_validation,
            'dump_inputs': self.dump_inputs,
            'dump_memory': self.dump_memory,
            'ignore_clause_types': list(self.ignore_clause_types),
            'require_clause_types': list(self.require_clause_types)
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 37: CONFIGURATION VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

class ConfigurationValidator:
    """
    Validates configuration correctness.
    
    Ensures configuration values are valid and compatible.
    """
    
    def validate(self, config: AdapterConfiguration) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (valid, error_messages)
        """
        errors = []
        
        # Validate optimization level
        if not 0 <= config.performance_profile.optimization_level <= 3:
            errors.append("optimization_level must be 0-3")
        
        # Validate clause timeout
        if config.performance_profile.clause_timeout_ms <= 0:
            errors.append("clause_timeout_ms must be positive")
        
        # Validate max violations
        if config.enforcement_policy.max_violations < 0:
            errors.append("max_violations must be non-negative")
        
        # Check conflicting options
        if config.performance_profile.lazy_validation and config.enforcement_policy.fail_fast:
            errors.append("lazy_validation incompatible with fail_fast")
        
        # Validate clause type sets
        common = config.ignore_clause_types & config.require_clause_types
        if common:
            errors.append(f"Clause types in both ignore and require: {common}")
        
        return (len(errors) == 0, errors)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 38: CONFIGURATION LOADER
# ════════════════════════════════════════════════════════════════════════════

class ConfigurationLoader:
    """
    Loads configuration from multiple sources.
    
    Supports JSON files, dictionaries, and environment variables.
    """
    
    def __init__(self):
        self.validator = ConfigurationValidator()
    
    def load_from_dict(
        self,
        config_dict: Dict[str, Any]
    ) -> AdapterConfiguration:
        """
        Load configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            AdapterConfiguration instance
        """
        config = AdapterConfiguration()
        
        # Load enforcement policy
        if 'enforcement_policy' in config_dict:
            policy_dict = config_dict['enforcement_policy']
            policy_type = PolicyType(policy_dict.get('policy_type', 'balanced'))
            
            config.enforcement_policy = EnforcementPolicy(
                policy_type=policy_type,
                fail_fast=policy_dict.get('fail_fast', True),
                treat_advisory_as_mandatory=policy_dict.get('treat_advisory_as_mandatory', False),
                allow_missing_clauses=policy_dict.get('allow_missing_clauses', True),
                max_violations=policy_dict.get('max_violations', 0)
            )
        
        # Load performance profile
        if 'performance_profile' in config_dict:
            perf_dict = config_dict['performance_profile']
            config.performance_profile = PerformanceProfile(
                optimization_level=perf_dict.get('optimization_level', 1),
                enable_caching=perf_dict.get('enable_caching', False),
                parallel_validation=perf_dict.get('parallel_validation', False),
                clause_timeout_ms=perf_dict.get('clause_timeout_ms', 1000)
            )
        
        # Load debugging options
        config.verbose_logging = config_dict.get('verbose_logging', False)
        config.trace_validation = config_dict.get('trace_validation', False)
        
        # Validate loaded config
        valid, errors = self.validator.validate(config)
        if not valid:
            raise ValueError(f"Invalid configuration: {errors}")
        
        return config
    
    def load_from_file(self, file_path: Union[str, Path]) -> AdapterConfiguration:
        """
        Load configuration from JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            AdapterConfiguration instance
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return self.load_from_dict(config_dict)
    
    def load_from_env(
        self,
        prefix: str = "ADAPTER_"
    ) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix
            
        Returns:
            Configuration dictionary
        """
        import os
        config = {}
        
        # Map environment variables to config
        env_map = {
            f'{prefix}POLICY': 'enforcement_policy.policy_type',
            f'{prefix}FAIL_FAST': 'enforcement_policy.fail_fast',
            f'{prefix}OPTIMIZATION': 'performance_profile.optimization_level',
            f'{prefix}VERBOSE': 'verbose_logging'
        }
        
        for env_var, config_path in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Parse value
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                
                # Set nested config
                keys = config_path.split('.')
                current = config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = value
        
        return config


# ════════════════════════════════════════════════════════════════════════════
# SECTION 39: POLICY REGISTRY
# ════════════════════════════════════════════════════════════════════════════

class PolicyRegistry:
    """
    Registry for named enforcement policies.
    
    Allows policies to be registered, retrieved, and shared across adapters.
    """
    
    def __init__(self):
        self.policies: Dict[str, EnforcementPolicy] = {
            'strict': EnforcementPolicy.strict(),
            'balanced': EnforcementPolicy.balanced(),
            'permissive': EnforcementPolicy.permissive()
        }
    
    def register(self, name: str, policy: EnforcementPolicy) -> None:
        """
        Register named policy.
        
        Args:
            name: Policy name
            policy: EnforcementPolicy instance
        """
        self.policies[name] = policy
    
    def get(self, name: str) -> Optional[EnforcementPolicy]:
        """
        Get policy by name.
        
        Args:
            name: Policy name
            
        Returns:
            EnforcementPolicy or None if not found
        """
        return self.policies.get(name)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister policy.
        
        Args:
            name: Policy name
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self.policies:
            del self.policies[name]
            return True
        return False
    
    def list_policies(self) -> List[str]:
        """Get list of registered policy names."""
        return list(self.policies.keys())


# ════════════════════════════════════════════════════════════════════════════
# SECTION 40: CONFIGURATION MANAGER
# ════════════════════════════════════════════════════════════════════════════

class ConfigurationManager:
    """
    Central configuration management.
    
    Coordinates configuration loading, validation, and runtime updates.
    """
    
    def __init__(self):
        self.loader = ConfigurationLoader()
        self.validator = ConfigurationValidator()
        self.policy_registry = PolicyRegistry()
        self.active_config: Optional[AdapterConfiguration] = None
    
    def load_configuration(
        self,
        source: Union[str, Path, Dict[str, Any]]
    ) -> AdapterConfiguration:
        """
        Load configuration from source.
        
        Args:
            source: File path, dict, or config object
            
        Returns:
            Loaded AdapterConfiguration
        """
        if isinstance(source, dict):
            config = self.loader.load_from_dict(source)
        elif isinstance(source, (str, Path)):
            config = self.loader.load_from_file(source)
        else:
            raise ValueError(f"Invalid config source type: {type(source)}")
        
        self.active_config = config
        return config
    
    def get_active_config(self) -> AdapterConfiguration:
        """Get currently active configuration."""
        if self.active_config is None:
            self.active_config = AdapterConfiguration()
        return self.active_config
    
    def update_config(
        self,
        updates: Dict[str, Any]
    ) -> AdapterConfiguration:
        """
        Update active configuration.
        
        Args:
            updates: Configuration updates
            
        Returns:
            Updated configuration
        """
        config = self.get_active_config()
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Validate updated config
        valid, errors = self.validator.validate(config)
        if not valid:
            raise ValueError(f"Invalid configuration updates: {errors}")
        
        return config
    
    def add_function_override(
        self,
        function_name: str,
        overrides: Dict[str, Any]
    ) -> None:
        """
        Add function-specific configuration overrides.
        
        Args:
            function_name: Function name
            overrides: Configuration overrides
        """
        config = self.get_active_config()
        config.function_overrides[function_name] = overrides


# ════════════════════════════════════════════════════════════════════════════
# SECTION 41: PYTHON TYPE MAPPER
# ════════════════════════════════════════════════════════════════════════════

class PythonTypeMapper:
    """
    Maps between Python types and C types.
    
    Provides bidirectional mapping for ctypes and cffi integration.
    """
    
    def __init__(self):
        # Python type -> C type name mapping
        self.python_to_c: Dict[type, str] = {
            int: 'int',
            float: 'double',
            bool: 'bool',
            str: 'char*',
            bytes: 'char*',
            type(None): 'void*'
        }
        
        # C type name -> Python type mapping
        self.c_to_python: Dict[str, type] = {
            'int': int,
            'int32_t': int,
            'uint32_t': int,
            'int64_t': int,
            'uint64_t': int,
            'float': float,
            'double': float,
            'bool': bool,
            'char*': bytes,
            'const char*': bytes,
            'void*': int  # Pointer as integer address
        }
    
    def get_c_type(self, python_type: type) -> Optional[str]:
        """
        Get C type name for Python type.
        
        Args:
            python_type: Python type
            
        Returns:
            C type name or None
        """
        return self.python_to_c.get(python_type)
    
    def get_python_type(self, c_type_name: str) -> Optional[type]:
        """
        Get Python type for C type name.
        
        Args:
            c_type_name: C type name
            
        Returns:
            Python type or None
        """
        return self.c_to_python.get(c_type_name)
    
    def is_pointer_type(self, c_type_name: str) -> bool:
        """
        Check if C type is a pointer.
        
        Args:
            c_type_name: C type name
            
        Returns:
            True if pointer type
        """
        return '*' in c_type_name or 'ptr' in c_type_name.lower()
    
    def register_mapping(
        self,
        python_type: type,
        c_type_name: str
    ) -> None:
        """
        Register custom type mapping.
        
        Args:
            python_type: Python type
            c_type_name: C type name
        """
        self.python_to_c[python_type] = c_type_name
        self.c_to_python[c_type_name] = python_type
    
    def get_all_c_types(self) -> List[str]:
        """Get all registered C type names."""
        return list(self.c_to_python.keys())
    
    def get_all_python_types(self) -> List[type]:
        """Get all registered Python types."""
        return list(self.python_to_c.keys())


# ════════════════════════════════════════════════════════════════════════════
# SECTION 42: PYTHON NORMALIZER
# ════════════════════════════════════════════════════════════════════════════

class PythonNormalizer(NormalizationInterface):
    """
    Python-specific value normalization.
    
    Converts Python objects to canonical forms suitable for validation
    and native invocation.
    """
    
    def __init__(self):
        super().__init__()
        self.type_mapper = PythonTypeMapper()
    
    def normalize_value(self, value: Any) -> Any:
        """
        Normalize single Python value.
        
        Args:
            value: Python value
            
        Returns:
            Normalized value
        """
        # None remains None
        if value is None:
            return None
        
        # Integers: check for overflow concerns (validation handles this)
        if isinstance(value, bool):
            # bool is subclass of int, handle separately
            return 1 if value else 0
        
        if isinstance(value, int):
            return value
        
        # Floats pass through
        if isinstance(value, float):
            return value
        
        # Strings: keep as-is for now (encoding happens at call boundary)
        if isinstance(value, str):
            return value
        
        # Bytes: keep as-is
        if isinstance(value, bytes):
            return value
        
        # Bytearray: convert to bytes for consistency
        if isinstance(value, bytearray):
            return bytes(value)
        
        # Memoryview: convert to bytes
        if isinstance(value, memoryview):
            return bytes(value)
        
        # ctypes types: extract value or address
        try:
            import ctypes
            if isinstance(value, ctypes._Pointer):
                # Extract pointer address
                return ctypes.addressof(value.contents)
            elif isinstance(value, ctypes._SimpleCData):
                # Extract value from ctypes type
                return value.value
        except ImportError:
            pass
        
        # Default: return as-is
        return value
    
    def normalize_buffer(
        self,
        buffer: Any
    ) -> Tuple[Optional[bytes], int]:
        """
        Normalize buffer to bytes and length.
        
        Args:
            buffer: Buffer object
            
        Returns:
            Tuple of (bytes, length)
        """
        if buffer is None:
            return (None, 0)
        
        if isinstance(buffer, bytes):
            return (buffer, len(buffer))
        
        if isinstance(buffer, bytearray):
            return (bytes(buffer), len(buffer))
        
        if isinstance(buffer, memoryview):
            return (bytes(buffer), len(buffer))
        
        if isinstance(buffer, str):
            # Encode string to bytes
            encoded = buffer.encode('utf-8')
            return (encoded, len(encoded))
        
        # Try to get buffer interface
        try:
            mv = memoryview(buffer)
            return (bytes(mv), len(mv))
        except TypeError:
            return (None, 0)
    
    def get_type_mapper(self) -> 'PythonTypeMapper':
        """Get the associated type mapper."""
        return self.type_mapper


# ════════════════════════════════════════════════════════════════════════════
# SECTION 43: PYTHON SIGNATURE MIRROR
# ════════════════════════════════════════════════════════════════════════════

class PythonSignatureMirror:
    """
    Mirrors C function signatures from contracts for Python FFI.
    
    Reconstructs exact function signatures for ctypes/cffi usage.
    """
    
    def __init__(self):
        self.type_mapper = PythonTypeMapper()
    
    def build_signature(
        self,
        function_contract: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build function signature from contract.
        
        Args:
            function_contract: Function contract dictionary
            
        Returns:
            Signature dictionary with types and calling convention
        """
        signature: Dict[str, Any] = {
            'name': function_contract.get('name', 'unknown'),
            'parameters': [],
            'return_type': 'void',
            'calling_convention': 'cdecl'
        }
        
        # Extract parameter types
        for param in function_contract.get('parameters', []):
            param_info = {
                'name': param.get('name', ''),
                'c_type': param.get('type', 'int'),
                'python_type': self.type_mapper.get_python_type(
                    param.get('type', 'int')
                )
            }
            signature['parameters'].append(param_info)
        
        # Extract return type
        return_info = function_contract.get('return', {})
        if return_info:
            signature['return_type'] = return_info.get('type', 'void')
        
        # Extract calling convention
        signature['calling_convention'] = function_contract.get(
            'calling_convention',
            'cdecl'
        )
        
        return signature
    
    def get_ctypes_signature(
        self,
        signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert signature to ctypes-compatible form.
        
        Args:
            signature: Signature dictionary
            
        Returns:
            ctypes-compatible signature
        """
        try:
            import ctypes
            
            # Map C types to ctypes types
            type_map = {
                'int': ctypes.c_int,
                'int32_t': ctypes.c_int32,
                'uint32_t': ctypes.c_uint32,
                'int64_t': ctypes.c_int64,
                'float': ctypes.c_float,
                'double': ctypes.c_double,
                'char*': ctypes.c_char_p,
                'void*': ctypes.c_void_p,
                'bool': ctypes.c_bool
            }
            
            argtypes = []
            for param in signature['parameters']:
                c_type = param['c_type']
                ctypes_type = type_map.get(c_type, ctypes.c_int)
                argtypes.append(ctypes_type)
            
            restype = type_map.get(signature['return_type'], None)
            
            return {
                'argtypes': argtypes,
                'restype': restype
            }
        except ImportError:
            return {'argtypes': [], 'restype': None}
    
    def get_cffi_cdef(
        self,
        signature: Dict[str, Any]
    ) -> str:
        """
        Build cffi cdef string from signature.
        
        Args:
            signature: Function signature
            
        Returns:
            C definition string
        """
        params = []
        for param in signature['parameters']:
            params.append(f"{param['c_type']} {param['name']}")
        
        params_str = ', '.join(params) if params else 'void'
        return f"{signature['return_type']} {signature['name']}({params_str});"


# ════════════════════════════════════════════════════════════════════════════
# SECTION 44: CTYPES INTEGRATION
# ════════════════════════════════════════════════════════════════════════════

class CtypesIntegration:
    """
    Integration layer for ctypes-based FFI.
    
    Wraps ctypes function calls with enforcement pipeline.
    """
    
    def __init__(self):
        self.signature_mirror = PythonSignatureMirror()
        self.loaded_libraries: Dict[str, Any] = {}
    
    def load_library(
        self,
        library_path: str,
        calling_convention: str = 'cdecl'
    ) -> Any:
        """
        Load native library using ctypes.
        
        Args:
            library_path: Path to shared library
            calling_convention: Calling convention (cdecl/stdcall)
            
        Returns:
            ctypes library object
        """
        try:
            import ctypes
            
            if calling_convention == 'stdcall':
                lib = ctypes.WinDLL(library_path)
            else:
                lib = ctypes.CDLL(library_path)
            
            self.loaded_libraries[library_path] = lib
            return lib
        except ImportError:
            raise RuntimeError("ctypes not available")
        except OSError as e:
            raise RuntimeError(f"Failed to load library: {e}")
    
    def configure_function(
        self,
        library: Any,
        function_name: str,
        signature: Dict[str, Any]
    ) -> Any:
        """
        Configure ctypes function with signature.
        
        Args:
            library: ctypes library object
            function_name: Function name
            signature: Function signature
            
        Returns:
            Configured function object
        """
        if not hasattr(library, function_name):
            raise ValueError(f"Function not found: {function_name}")
        
        func = getattr(library, function_name)
        
        # Apply ctypes signature
        ctypes_sig = self.signature_mirror.get_ctypes_signature(signature)
        func.argtypes = ctypes_sig['argtypes']
        func.restype = ctypes_sig['restype']
        
        return func
    
    def get_loaded_libraries(self) -> List[str]:
        """Get list of loaded library paths."""
        return list(self.loaded_libraries.keys())


# ════════════════════════════════════════════════════════════════════════════
# SECTION 45: CFFI INTEGRATION
# ════════════════════════════════════════════════════════════════════════════

class CffiIntegration:
    """
    Integration layer for cffi-based FFI.
    
    Wraps cffi function calls with enforcement pipeline.
    """
    
    def __init__(self):
        self.ffi = None
        self.loaded_libraries: Dict[str, Any] = {}
    
    def initialize_ffi(self) -> None:
        """Initialize cffi FFI instance."""
        try:
            from cffi import FFI
            self.ffi = FFI()
        except ImportError:
            raise RuntimeError("cffi not available")
    
    def load_library(
        self,
        library_path: str,
        definitions: str
    ) -> Any:
        """
        Load native library using cffi.
        
        Args:
            library_path: Path to shared library
            definitions: C function definitions
            
        Returns:
            cffi library object
        """
        if self.ffi is None:
            self.initialize_ffi()
        
        # Define C signatures
        self.ffi.cdef(definitions)
        
        # Load library
        lib = self.ffi.dlopen(library_path)
        self.loaded_libraries[library_path] = lib
        
        return lib
    
    def build_cdef_from_signature(
        self,
        signature: Dict[str, Any]
    ) -> str:
        """
        Build cffi cdef string from signature.
        
        Args:
            signature: Function signature
            
        Returns:
            C definition string
        """
        params = []
        for param in signature['parameters']:
            params.append(f"{param['c_type']} {param['name']}")
        
        params_str = ', '.join(params) if params else 'void'
        
        return f"{signature['return_type']} {signature['name']}({params_str});"
    
    def get_loaded_libraries(self) -> List[str]:
        """Get list of loaded library paths."""
        return list(self.loaded_libraries.keys())


# ════════════════════════════════════════════════════════════════════════════
# SECTION 46: PYTHON ADAPTER
# ════════════════════════════════════════════════════════════════════════════

class PythonAdapter(LanguageAdapter):
    """
    Python-specific language adapter.
    
    Integrates Python normalization, ctypes/cffi support, and enforcement
    pipeline for Python-to-native FFI calls.
    """
    
    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        ffi_mode: str = 'ctypes'
    ):
        """
        Initialize Python adapter.
        
        Args:
            config: Adapter configuration
            ffi_mode: FFI mechanism ('ctypes' or 'cffi')
        """
        super().__init__(config)
        
        self.ffi_mode = ffi_mode
        self.normalizer = PythonNormalizer()
        self.signature_mirror = PythonSignatureMirror()
        
        # Initialize FFI integration
        if ffi_mode == 'ctypes':
            self.ffi_integration = CtypesIntegration()
        elif ffi_mode == 'cffi':
            self.ffi_integration = CffiIntegration()
        else:
            raise ValueError(f"Invalid FFI mode: {ffi_mode}")
        
        # Initialize memory manager
        self.memory_manager = PythonMemoryManager()
        
        # Initialize exception handling (uses forward-declared classes)
        self._exception_translator = None
        self._crash_handler = None
        self._recovery_handler = None
    
    @property
    def exception_translator(self):
        """Lazy-init PythonExceptionTranslator."""
        if self._exception_translator is None:
            self._exception_translator = PythonExceptionTranslator()
        return self._exception_translator
    
    @property
    def crash_handler(self):
        """Lazy-init PythonCrashHandler."""
        if self._crash_handler is None:
            self._crash_handler = PythonCrashHandler()
        return self._crash_handler
    
    @property
    def recovery_handler(self):
        """Lazy-init ErrorRecoveryHandler."""
        if self._recovery_handler is None:
            self._recovery_handler = ErrorRecoveryHandler()
        return self._recovery_handler
    
    def load_native_library(
        self,
        library_path: str,
        definitions: Optional[str] = None
    ) -> Any:
        """
        Load native library.
        
        Args:
            library_path: Path to shared library
            definitions: C definitions (cffi only)
            
        Returns:
            Library object
        """
        if self.ffi_mode == 'ctypes':
            return self.ffi_integration.load_library(library_path)
        elif self.ffi_mode == 'cffi':
            if definitions is None:
                raise ValueError("cffi requires C definitions")
            return self.ffi_integration.load_library(library_path, definitions)
    
    def normalize_for_call(
        self,
        inputs: List[Any]
    ) -> List[Any]:
        """
        Normalize inputs for native call.
        
        Args:
            inputs: Python values
            
        Returns:
            Normalized values
        """
        return self.normalizer.normalize_inputs(inputs)
    
    def call(
        self,
        function_name: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Call native function with enforcement.
        
        Args:
            function_name: Function name
            *args: Function arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        # Convert args to list and normalize
        inputs = list(args)
        normalized = self.normalize_for_call(inputs)
        
        # Get validation graph
        graph = self.get_validation_graph(function_name)
        if graph:
            # Create enforcement context
            context = self.create_enforcement_context(function_name)
            context.normalized_inputs = normalized
            
            # Run pre-validation
            result = self.validation_engine.validate_with_metrics(
                graph, normalized, context
            )
            
            if not result.get('all_passed', True):
                raise RuntimeError(
                    f"Pre-call validation failed for {function_name}"
                )
        
        # Return normalized inputs (actual call would happen here)
        return {'normalized_inputs': normalized, 'function': function_name}
    
    def get_function_signature(
        self,
        function_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get function signature from loaded contract.
        
        Args:
            function_name: Function name
            
        Returns:
            Signature dictionary or None
        """
        graph = self.get_validation_graph(function_name)
        if not graph:
            return None
        
        return {
            'name': function_name,
            'parameters': [],
            'return_type': 'int'
        }
    
    def prepare_buffer_parameter(
        self,
        buffer_obj: Any
    ) -> 'PythonPointerWrapper':
        """
        Prepare buffer parameter for native call.
        
        Args:
            buffer_obj: Python buffer object
            
        Returns:
            PythonPointerWrapper for the buffer
        """
        return self.memory_manager.wrap_buffer(buffer_obj)
    
    def get_normalizer(self) -> PythonNormalizer:
        """Get the Python normalizer."""
        return self.normalizer
    
    def get_ffi_mode(self) -> str:
        """Get the current FFI mode."""
        return self.ffi_mode


# ════════════════════════════════════════════════════════════════════════════
# SECTION 47: PYTHON POINTER WRAPPER
# ════════════════════════════════════════════════════════════════════════════

class PythonPointerWrapper:
    """
    Safe wrapper for native pointers in Python.
    
    Tracks pointer address, size, ownership, and validity to prevent
    use-after-free and double-free errors.
    """
    
    def __init__(
        self,
        address: int,
        size: int = 0,
        ownership: OwnershipKind = OwnershipKind.UNKNOWN,
        python_object: Optional[Any] = None
    ):
        """
        Initialize pointer wrapper.
        
        Args:
            address: Pointer address
            size: Allocated size in bytes
            ownership: Ownership kind
            python_object: Associated Python object (for pinning)
        """
        self.address = address
        self.size = size
        self.ownership = ownership
        self.python_object = python_object
        self._freed = False
        self._valid = True
    
    def is_valid(self) -> bool:
        """Check if pointer is still valid."""
        return self._valid and not self._freed
    
    def mark_freed(self) -> None:
        """Mark pointer as freed."""
        if self._freed:
            raise RuntimeError(f"Double-free detected: {hex(self.address)}")
        self._freed = True
        self._valid = False
    
    def invalidate(self) -> None:
        """Invalidate pointer without freeing."""
        self._valid = False
    
    def get_address(self) -> int:
        """
        Get pointer address.
        
        Returns:
            Pointer address
            
        Raises:
            RuntimeError: If pointer is invalid
        """
        if not self.is_valid():
            raise RuntimeError(f"Invalid pointer: {hex(self.address)}")
        return self.address
    
    def __int__(self) -> int:
        """Convert to integer address."""
        return self.get_address()
    
    def __repr__(self) -> str:
        """String representation."""
        status = "valid" if self.is_valid() else "invalid"
        return f"<Pointer {hex(self.address)} size={self.size} {status}>"


# ════════════════════════════════════════════════════════════════════════════
# SECTION 48: BUFFER PINNER
# ════════════════════════════════════════════════════════════════════════════

class BufferPinner:
    """
    Pins Python buffers during native calls.
    
    Ensures buffer memory remains valid and unmoved during native execution.
    """
    
    def __init__(self):
        self.pinned_buffers: Dict[int, Any] = {}
    
    def pin_buffer(self, buffer_obj: Any) -> Tuple[int, int]:
        """
        Pin buffer and return address and size.
        
        Args:
            buffer_obj: Python buffer object
            
        Returns:
            Tuple of (address, size)
            
        Raises:
            ValueError: If object is not a buffer
        """
        if isinstance(buffer_obj, bytes):
            address = id(buffer_obj)
            size = len(buffer_obj)
            self.pinned_buffers[address] = buffer_obj
            return (address, size)
        
        elif isinstance(buffer_obj, bytearray):
            address = id(buffer_obj)
            size = len(buffer_obj)
            self.pinned_buffers[address] = buffer_obj
            return (address, size)
        
        elif isinstance(buffer_obj, memoryview):
            address = id(buffer_obj.obj)
            size = len(buffer_obj)
            self.pinned_buffers[address] = buffer_obj.obj
            return (address, size)
        
        else:
            # Try buffer protocol
            try:
                mv = memoryview(buffer_obj)
                address = id(mv.obj)
                size = len(mv)
                self.pinned_buffers[address] = mv.obj
                return (address, size)
            except TypeError:
                raise ValueError(f"Object is not a buffer: {type(buffer_obj)}")
    
    def unpin_buffer(self, address: int) -> bool:
        """
        Unpin buffer.
        
        Args:
            address: Buffer address
            
        Returns:
            True if buffer was pinned
        """
        if address in self.pinned_buffers:
            del self.pinned_buffers[address]
            return True
        return False
    
    def unpin_all(self) -> None:
        """Unpin all buffers."""
        self.pinned_buffers.clear()
    
    def is_pinned(self, address: int) -> bool:
        """Check if buffer is pinned."""
        return address in self.pinned_buffers
    
    def get_pinned_count(self) -> int:
        """Get number of pinned buffers."""
        return len(self.pinned_buffers)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 49: ALLOCATION TRACKER
# ════════════════════════════════════════════════════════════════════════════

class AllocationTracker:
    """
    Tracks FFI allocations and ownership.
    
    Records allocations crossing FFI boundary to detect leaks and
    enforce ownership semantics.
    """
    
    def __init__(self):
        self.allocations: Dict[int, Dict[str, Any]] = {}
        self.allocation_count: int = 0
    
    def track_allocation(
        self,
        address: int,
        size: int,
        source: str,
        ownership: OwnershipKind,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track new allocation.
        
        Args:
            address: Memory address
            size: Allocation size
            source: Allocation source ('python' or 'native')
            ownership: Ownership kind
            metadata: Optional metadata
        """
        self.allocations[address] = {
            'address': address,
            'size': size,
            'source': source,
            'ownership': ownership,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'freed': False,
            'metadata': metadata or {}
        }
        self.allocation_count += 1
    
    def mark_freed(self, address: int) -> None:
        """
        Mark allocation as freed.
        
        Args:
            address: Memory address
            
        Raises:
            ValueError: If allocation not tracked or already freed
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        if self.allocations[address]['freed']:
            raise ValueError(f"Double-free detected: {hex(address)}")
        
        self.allocations[address]['freed'] = True
        self.allocations[address]['freed_at'] = (
            datetime.utcnow().isoformat() + 'Z'
        )
    
    def transfer_ownership(
        self,
        address: int,
        new_ownership: OwnershipKind
    ) -> None:
        """
        Transfer allocation ownership.
        
        Args:
            address: Memory address
            new_ownership: New ownership kind
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        old_ownership = self.allocations[address]['ownership']
        self.allocations[address]['ownership'] = new_ownership
        self.allocations[address]['ownership_transferred'] = {
            'from': old_ownership.value,
            'to': new_ownership.value,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def get_allocation(self, address: int) -> Optional[Dict[str, Any]]:
        """Get allocation information."""
        return self.allocations.get(address)
    
    def get_active_allocations(self) -> List[Dict[str, Any]]:
        """Get list of active (not freed) allocations."""
        return [
            alloc for alloc in self.allocations.values()
            if not alloc['freed']
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get allocation statistics."""
        active = self.get_active_allocations()
        
        return {
            'total_allocations': self.allocation_count,
            'active_allocations': len(active),
            'freed_allocations': len(
                [a for a in self.allocations.values() if a['freed']]
            ),
            'total_bytes_active': sum(a['size'] for a in active),
            'by_source': {
                'python': len(
                    [a for a in active if a['source'] == 'python']
                ),
                'native': len(
                    [a for a in active if a['source'] == 'native']
                )
            }
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 50: REFERENCE HOLDER
# ════════════════════════════════════════════════════════════════════════════

class ReferenceHolder:
    """
    Holds references to Python objects during native calls.
    
    Prevents garbage collection of objects whose pointers are in use.
    """
    
    def __init__(self):
        self.held_references: List[Any] = []
    
    def hold(self, obj: Any) -> None:
        """
        Hold reference to object.
        
        Args:
            obj: Object to hold
        """
        self.held_references.append(obj)
    
    def release(self, obj: Any) -> bool:
        """
        Release reference to object.
        
        Args:
            obj: Object to release
            
        Returns:
            True if object was held
        """
        try:
            self.held_references.remove(obj)
            return True
        except ValueError:
            return False
    
    def release_all(self) -> None:
        """Release all held references."""
        self.held_references.clear()
    
    def is_held(self, obj: Any) -> bool:
        """Check if object is held."""
        return obj in self.held_references
    
    def get_count(self) -> int:
        """Get number of held references."""
        return len(self.held_references)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release all."""
        self.release_all()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 51: MEMORY VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

class MemoryValidator:
    """
    Validates memory operations for safety.
    
    Checks buffer bounds, alignment, and access patterns.
    """
    
    def validate_buffer_access(
        self,
        buffer_address: int,
        buffer_size: int,
        access_offset: int,
        access_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate buffer access within bounds.
        
        Args:
            buffer_address: Buffer base address
            buffer_size: Buffer size in bytes
            access_offset: Access offset from base
            access_size: Access size in bytes
            
        Returns:
            Tuple of (valid, error_message)
        """
        if access_offset < 0:
            return (False, f"Negative offset: {access_offset}")
        
        if access_size < 0:
            return (False, f"Negative size: {access_size}")
        
        if access_offset + access_size > buffer_size:
            return (
                False,
                f"Access beyond buffer bounds: offset={access_offset} "
                f"size={access_size} buffer_size={buffer_size}"
            )
        
        return (True, None)
    
    def validate_alignment(
        self,
        address: int,
        required_alignment: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate address alignment.
        
        Args:
            address: Memory address
            required_alignment: Required alignment in bytes
            
        Returns:
            Tuple of (valid, error_message)
        """
        if required_alignment <= 0:
            return (False, f"Invalid alignment: {required_alignment}")
        
        if (address % required_alignment) != 0:
            return (
                False,
                f"Address {hex(address)} not aligned to "
                f"{required_alignment} bytes"
            )
        
        return (True, None)
    
    def validate_pointer_not_null(
        self,
        address: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate pointer is not null.
        
        Args:
            address: Pointer address
            
        Returns:
            Tuple of (valid, error_message)
        """
        if address == 0:
            return (False, "Null pointer")
        
        return (True, None)
    
    def validate_size_positive(
        self,
        size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate size is positive.
        
        Args:
            size: Size value
            
        Returns:
            Tuple of (valid, error_message)
        """
        if size <= 0:
            return (False, f"Non-positive size: {size}")
        return (True, None)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 52: PYTHON MEMORY MANAGER
# ════════════════════════════════════════════════════════════════════════════

class PythonMemoryManager:
    """
    Unified memory management for Python FFI.
    
    Coordinates buffer pinning, allocation tracking, reference holding,
    and memory validation.
    """
    
    def __init__(self):
        self.buffer_pinner = BufferPinner()
        self.allocation_tracker = AllocationTracker()
        self.reference_holder = ReferenceHolder()
        self.memory_validator = MemoryValidator()
        self.pointer_wrappers: Dict[int, PythonPointerWrapper] = {}
    
    def wrap_buffer(
        self,
        buffer_obj: Any,
        ownership: OwnershipKind = OwnershipKind.CALLER_OWNED
    ) -> PythonPointerWrapper:
        """
        Wrap Python buffer as pointer.
        
        Args:
            buffer_obj: Python buffer object
            ownership: Ownership kind
            
        Returns:
            PythonPointerWrapper
        """
        # Pin buffer
        address, size = self.buffer_pinner.pin_buffer(buffer_obj)
        
        # Track allocation
        self.allocation_tracker.track_allocation(
            address,
            size,
            'python',
            ownership,
            {'type': 'buffer', 'python_type': type(buffer_obj).__name__}
        )
        
        # Hold reference
        self.reference_holder.hold(buffer_obj)
        
        # Create wrapper
        wrapper = PythonPointerWrapper(
            address,
            size,
            ownership,
            buffer_obj
        )
        
        self.pointer_wrappers[address] = wrapper
        return wrapper
    
    def wrap_native_pointer(
        self,
        address: int,
        size: int,
        ownership: OwnershipKind = OwnershipKind.CALLEE_OWNED
    ) -> PythonPointerWrapper:
        """
        Wrap native pointer.
        
        Args:
            address: Pointer address
            size: Allocation size
            ownership: Ownership kind
            
        Returns:
            PythonPointerWrapper
        """
        # Track allocation
        self.allocation_tracker.track_allocation(
            address,
            size,
            'native',
            ownership,
            {'type': 'native_pointer'}
        )
        
        # Create wrapper
        wrapper = PythonPointerWrapper(address, size, ownership)
        self.pointer_wrappers[address] = wrapper
        
        return wrapper
    
    def free_pointer(self, wrapper: PythonPointerWrapper) -> None:
        """
        Free pointer and cleanup.
        
        Args:
            wrapper: PythonPointerWrapper to free
        """
        address = wrapper.address
        
        # Mark allocation as freed
        self.allocation_tracker.mark_freed(address)
        
        # Mark wrapper as freed
        wrapper.mark_freed()
        
        # Unpin if buffer
        if wrapper.python_object is not None:
            self.buffer_pinner.unpin_buffer(address)
            self.reference_holder.release(wrapper.python_object)
        
        # Remove wrapper
        if address in self.pointer_wrappers:
            del self.pointer_wrappers[address]
    
    def get_pointer_wrapper(
        self,
        address: int
    ) -> Optional[PythonPointerWrapper]:
        """Get pointer wrapper by address."""
        return self.pointer_wrappers.get(address)
    
    def validate_buffer_access(
        self,
        wrapper: PythonPointerWrapper,
        offset: int,
        size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate buffer access.
        
        Args:
            wrapper: PythonPointerWrapper
            offset: Access offset
            size: Access size
            
        Returns:
            Tuple of (valid, error_message)
        """
        return self.memory_validator.validate_buffer_access(
            wrapper.address,
            wrapper.size,
            offset,
            size
        )
    
    def cleanup(self) -> None:
        """Cleanup all resources."""
        self.buffer_pinner.unpin_all()
        self.reference_holder.release_all()
        self.pointer_wrappers.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory management statistics."""
        return {
            'allocation_tracker': self.allocation_tracker.get_statistics(),
            'pinned_buffers': len(self.buffer_pinner.pinned_buffers),
            'held_references': len(self.reference_holder.held_references),
            'active_wrappers': len(self.pointer_wrappers)
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 53: EXCEPTION HIERARCHY
# ════════════════════════════════════════════════════════════════════════════

class AdapterException(Exception):
    """
    Base exception for all adapter errors.
    
    Carries enforcement context and provides rich diagnostic information.
    """
    
    def __init__(
        self,
        message: str,
        enforcement_context: Optional[EnforcementContext] = None,
        remediation_hints: Optional[List[str]] = None
    ):
        """
        Initialize adapter exception.
        
        Args:
            message: Error message
            enforcement_context: Optional enforcement context
            remediation_hints: Optional remediation hints
        """
        super().__init__(message)
        self.enforcement_context = enforcement_context
        self.remediation_hints = remediation_hints or []
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
    
    def get_context_dict(self) -> Dict[str, Any]:
        """Get context as dictionary."""
        return {
            'message': str(self),
            'timestamp': self.timestamp,
            'enforcement_context': (
                self.enforcement_context.to_dict()
                if self.enforcement_context else None
            ),
            'remediation_hints': self.remediation_hints
        }


class ContractViolationError(AdapterException):
    """
    Exception raised when contract validation fails.
    
    Includes specific clause information and violation details.
    """
    
    def __init__(
        self,
        message: str,
        function_name: str,
        clause_id: str,
        expected: str,
        observed: str,
        enforcement_context: Optional[EnforcementContext] = None,
        remediation_hints: Optional[List[str]] = None
    ):
        super().__init__(message, enforcement_context, remediation_hints)
        self.function_name = function_name
        self.clause_id = clause_id
        self.expected = expected
        self.observed = observed
    
    def __str__(self) -> str:
        """Detailed string representation."""
        parts = [
            f"Contract violation in {self.function_name}",
            f"Clause: {self.clause_id}",
            f"Expected: {self.expected}",
            f"Observed: {self.observed}"
        ]
        
        if self.remediation_hints:
            parts.append(f"Hints: {', '.join(self.remediation_hints)}")
        
        return '\n'.join(parts)


class ParameterViolationError(ContractViolationError):
    """Exception for parameter validation failures."""
    
    def __init__(
        self,
        message: str,
        function_name: str,
        parameter_name: str,
        clause_id: str,
        expected: str,
        observed: str,
        **kwargs
    ):
        super().__init__(
            message, function_name, clause_id,
            expected, observed, **kwargs
        )
        self.parameter_name = parameter_name


class ReturnValueViolationError(ContractViolationError):
    """Exception for return value validation failures."""
    pass


class OwnershipViolationError(ContractViolationError):
    """Exception for ownership constraint violations."""
    pass


class NativeCrashError(AdapterException):
    """
    Exception raised when native code crashes.
    
    Includes crash context and native error information.
    """
    
    def __init__(
        self,
        message: str,
        crash_type: str,
        crash_address: Optional[int] = None,
        enforcement_context: Optional[EnforcementContext] = None,
        remediation_hints: Optional[List[str]] = None
    ):
        super().__init__(message, enforcement_context, remediation_hints)
        self.crash_type = crash_type
        self.crash_address = crash_address
    
    def __str__(self) -> str:
        """Detailed string representation."""
        parts = [f"Native crash: {self.crash_type}"]
        
        if self.crash_address is not None:
            parts.append(f"Address: {hex(self.crash_address)}")
        
        if self.remediation_hints:
            parts.append(f"Hints: {', '.join(self.remediation_hints)}")
        
        return '\n'.join(parts)


class SegmentationFaultError(NativeCrashError):
    """Exception for segmentation faults."""
    
    def __init__(
        self,
        message: str,
        crash_address: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message, 'segmentation_fault',
            crash_address, **kwargs
        )


class AccessViolationError(NativeCrashError):
    """Exception for access violations (Windows)."""
    
    def __init__(
        self,
        message: str,
        crash_address: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message, 'access_violation',
            crash_address, **kwargs
        )


class ConfigurationError(AdapterException):
    """Exception for configuration errors."""
    pass


# ════════════════════════════════════════════════════════════════════════════
# SECTION 54: EXCEPTION FORMATTER
# ════════════════════════════════════════════════════════════════════════════

class ExceptionFormatter:
    """
    Formats exceptions for human-readable output.
    
    Provides detailed, actionable error messages.
    """
    
    def format_contract_violation(
        self,
        error: ContractViolationError
    ) -> str:
        """
        Format contract violation error.
        
        Args:
            error: ContractViolationError instance
            
        Returns:
            Formatted error message
        """
        lines = []
        lines.append("=" * 70)
        lines.append("CONTRACT VIOLATION")
        lines.append("=" * 70)
        lines.append(f"Function: {error.function_name}")
        lines.append(f"Clause:   {error.clause_id}")
        lines.append(f"Time:     {error.timestamp}")
        lines.append("")
        lines.append("VIOLATION DETAILS:")
        lines.append(f"  Expected: {error.expected}")
        lines.append(f"  Observed: {error.observed}")
        
        if error.remediation_hints:
            lines.append("")
            lines.append("HOW TO FIX:")
            for hint in error.remediation_hints:
                lines.append(f"  * {hint}")
        
        if error.enforcement_context:
            lines.append("")
            lines.append("ENFORCEMENT CONTEXT:")
            lines.append(
                f"  Invocation ID: "
                f"{error.enforcement_context.invocation_id}"
            )
            lines.append(
                f"  Validations:   "
                f"{len(error.enforcement_context.validation_results)}"
            )
        
        lines.append("=" * 70)
        
        return '\n'.join(lines)
    
    def format_native_crash(
        self,
        error: NativeCrashError
    ) -> str:
        """
        Format native crash error.
        
        Args:
            error: NativeCrashError instance
            
        Returns:
            Formatted error message
        """
        lines = []
        lines.append("=" * 70)
        lines.append("NATIVE CRASH")
        lines.append("=" * 70)
        lines.append(f"Type:     {error.crash_type}")
        lines.append(f"Time:     {error.timestamp}")
        
        if error.crash_address is not None:
            lines.append(f"Address:  {hex(error.crash_address)}")
        
        if error.remediation_hints:
            lines.append("")
            lines.append("POSSIBLE CAUSES:")
            for hint in error.remediation_hints:
                lines.append(f"  * {hint}")
        
        lines.append("=" * 70)
        
        return '\n'.join(lines)
    
    def format_short(self, error: AdapterException) -> str:
        """
        Format exception as short one-line message.
        
        Args:
            error: AdapterException instance
            
        Returns:
            Short error message
        """
        if isinstance(error, ContractViolationError):
            return (
                f"{error.function_name}: {error.clause_id} failed "
                f"({error.expected} vs {error.observed})"
            )
        elif isinstance(error, NativeCrashError):
            return f"Native crash: {error.crash_type}"
        else:
            return str(error)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 55: ERROR RECOVERY HANDLER
# ════════════════════════════════════════════════════════════════════════════

class ErrorRecoveryStrategy(Enum):
    """Error recovery strategy."""
    PROPAGATE = "propagate"
    RETRY = "retry"
    FALLBACK = "fallback"
    IGNORE = "ignore"


class ErrorRecoveryHandler:
    """
    Manages error recovery strategies.
    
    Determines how to handle different error types.
    """
    
    def __init__(self):
        self.strategies: Dict[type, ErrorRecoveryStrategy] = {
            ContractViolationError: ErrorRecoveryStrategy.PROPAGATE,
            NativeCrashError: ErrorRecoveryStrategy.PROPAGATE,
            ConfigurationError: ErrorRecoveryStrategy.PROPAGATE
        }
        self.retry_counts: Dict[str, int] = {}
        self.max_retries: int = 3
    
    def register_strategy(
        self,
        exception_type: type,
        strategy: ErrorRecoveryStrategy
    ) -> None:
        """
        Register recovery strategy for exception type.
        
        Args:
            exception_type: Exception class
            strategy: Recovery strategy
        """
        self.strategies[exception_type] = strategy
    
    def get_strategy(
        self,
        exception: Exception
    ) -> ErrorRecoveryStrategy:
        """
        Get recovery strategy for exception.
        
        Args:
            exception: Exception instance
            
        Returns:
            Recovery strategy
        """
        exception_type = type(exception)
        
        # Check exact type match
        if exception_type in self.strategies:
            return self.strategies[exception_type]
        
        # Check parent classes
        for exc_type, strategy in self.strategies.items():
            if isinstance(exception, exc_type):
                return strategy
        
        # Default: propagate
        return ErrorRecoveryStrategy.PROPAGATE
    
    def should_retry(self, operation_id: str) -> bool:
        """
        Check if operation should be retried.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            True if retry allowed
        """
        count = self.retry_counts.get(operation_id, 0)
        return count < self.max_retries
    
    def record_retry(self, operation_id: str) -> None:
        """Record retry attempt."""
        self.retry_counts[operation_id] = (
            self.retry_counts.get(operation_id, 0) + 1
        )
    
    def reset_retries(self, operation_id: str) -> None:
        """Reset retry count for operation."""
        if operation_id in self.retry_counts:
            del self.retry_counts[operation_id]


# ════════════════════════════════════════════════════════════════════════════
# SECTION 56: PYTHON EXCEPTION TRANSLATOR
# ════════════════════════════════════════════════════════════════════════════

class PythonExceptionTranslator(ExceptionTranslator):
    """
    Python-specific exception translator.
    
    Translates crashes and violations into Python exception hierarchy.
    """
    
    def __init__(self):
        super().__init__()
        self.formatter = ExceptionFormatter()
    
    def translate_crash(
        self,
        crash_context: CrashContext,
        enforcement_context: Optional[EnforcementContext] = None
    ) -> NativeCrashError:
        """
        Translate crash context to Python exception.
        
        Args:
            crash_context: Crash context
            enforcement_context: Enforcement context
            
        Returns:
            NativeCrashError instance
        """
        # Extract remediation hints
        hints = self.extract_remediation_hints(crash_context)
        
        # Determine specific exception type
        if crash_context.exception_type in [
            'SegmentationFault', 'SIGSEGV'
        ]:
            return SegmentationFaultError(
                crash_context.exception_message,
                crash_context.faulting_address,
                enforcement_context=enforcement_context,
                remediation_hints=hints
            )
        
        elif crash_context.exception_type in [
            'AccessViolation', 'EXCEPTION_ACCESS_VIOLATION'
        ]:
            return AccessViolationError(
                crash_context.exception_message,
                crash_context.faulting_address,
                enforcement_context=enforcement_context,
                remediation_hints=hints
            )
        
        else:
            return NativeCrashError(
                crash_context.exception_message,
                crash_context.exception_type,
                crash_context.faulting_address,
                enforcement_context=enforcement_context,
                remediation_hints=hints
            )
    
    def translate_violation(
        self,
        violation_report: ViolationReport,
        enforcement_context: Optional[EnforcementContext] = None
    ) -> ContractViolationError:
        """
        Translate violation report to Python exception.
        
        Args:
            violation_report: Violation report
            enforcement_context: Enforcement context
            
        Returns:
            ContractViolationError instance
        """
        clause_type_lower = violation_report.clause_type.lower()
        
        if 'parameter' in clause_type_lower:
            return ParameterViolationError(
                violation_report.message,
                violation_report.function_name,
                'unknown',
                violation_report.clause_id,
                violation_report.expected,
                violation_report.observed,
                enforcement_context=enforcement_context,
                remediation_hints=violation_report.remediation_hints
            )
        
        elif 'return' in clause_type_lower:
            return ReturnValueViolationError(
                violation_report.message,
                violation_report.function_name,
                violation_report.clause_id,
                violation_report.expected,
                violation_report.observed,
                enforcement_context=enforcement_context,
                remediation_hints=violation_report.remediation_hints
            )
        
        elif 'ownership' in clause_type_lower:
            return OwnershipViolationError(
                violation_report.message,
                violation_report.function_name,
                violation_report.clause_id,
                violation_report.expected,
                violation_report.observed,
                enforcement_context=enforcement_context,
                remediation_hints=violation_report.remediation_hints
            )
        
        else:
            return ContractViolationError(
                violation_report.message,
                violation_report.function_name,
                violation_report.clause_id,
                violation_report.expected,
                violation_report.observed,
                enforcement_context=enforcement_context,
                remediation_hints=violation_report.remediation_hints
            )


# ════════════════════════════════════════════════════════════════════════════
# SECTION 57: PYTHON CRASH HANDLER
# ════════════════════════════════════════════════════════════════════════════

class PythonCrashHandler(CrashIsolationBoundary):
    """
    Python-specific crash handler.
    
    Captures Python exceptions and native crashes, translating to
    appropriate Python exception types.
    """
    
    def __init__(self):
        super().__init__()
        self.exception_translator = PythonExceptionTranslator()
    
    def execute_isolated(
        self,
        callable_func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[CrashContext]]:
        """
        Execute callable with crash isolation.
        
        Args:
            callable_func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (success, result, crash_context)
        """
        try:
            result = callable_func(*args, **kwargs)
            return (True, result, None)
        
        except MemoryError as e:
            crash_ctx = CrashContext(
                exception_type='MemoryError',
                exception_message=str(e),
                platform='python'
            )
            return (False, None, crash_ctx)
        
        except RecursionError as e:
            crash_ctx = CrashContext(
                exception_type='RecursionError',
                exception_message=str(e),
                platform='python'
            )
            return (False, None, crash_ctx)
        
        except OSError as e:
            crash_ctx = CrashContext(
                exception_type='OSError',
                exception_message=str(e),
                platform='python'
            )
            return (False, None, crash_ctx)
        
        except Exception as e:
            crash_ctx = CrashContext(
                exception_type=type(e).__name__,
                exception_message=str(e),
                platform='python'
            )
            return (False, None, crash_ctx)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 58: ENFORCEMENT SCOPE
# ════════════════════════════════════════════════════════════════════════════

class EnforcementScope:
    """
    Context manager for FFI invocation with automatic resource management.
    
    Ensures buffers are pinned, references held, and cleanup occurs even
    on exception paths.
    """
    
    def __init__(
        self,
        adapter: 'PythonAdapter',
        function_name: str
    ):
        """
        Initialize enforcement scope.
        
        Args:
            adapter: PythonAdapter instance
            function_name: Function to invoke
        """
        self.adapter = adapter
        self.function_name = function_name
        self.context: Optional[EnforcementContext] = None
        self.buffers: List[Any] = []
        self.wrappers: List[PythonPointerWrapper] = []
        self.active = False
    
    def __enter__(self) -> 'EnforcementScope':
        """Enter context - setup resources."""
        self.context = self.adapter.create_enforcement_context(
            self.function_name
        )
        self.active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - cleanup resources."""
        self.active = False
        
        # Cleanup wrappers and buffers
        for wrapper in self.wrappers:
            try:
                if wrapper.is_valid() and wrapper.python_object is not None:
                    self.adapter.memory_manager.buffer_pinner.unpin_buffer(
                        wrapper.address
                    )
                    self.adapter.memory_manager.reference_holder.release(
                        wrapper.python_object
                    )
            except Exception:
                pass  # Best effort cleanup
        
        self.buffers.clear()
        self.wrappers.clear()
        
        # Don't suppress exceptions
        return False
    
    def add_buffer(self, buffer_obj: Any) -> PythonPointerWrapper:
        """
        Add buffer to scope.
        
        Args:
            buffer_obj: Python buffer object
            
        Returns:
            PythonPointerWrapper for buffer
        """
        wrapper = self.adapter.memory_manager.wrap_buffer(buffer_obj)
        self.buffers.append(buffer_obj)
        self.wrappers.append(wrapper)
        return wrapper
    
    def invoke(self, *args) -> Any:
        """
        Invoke function within scope.
        
        Args:
            *args: Function arguments
            
        Returns:
            Function result
        """
        if not self.active:
            raise RuntimeError("EnforcementScope not active")
        
        return self.adapter.call(self.function_name, *args)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 59: DIAGNOSTIC COLLECTOR
# ════════════════════════════════════════════════════════════════════════════

class DiagnosticCollector:
    """
    Collects diagnostic information during enforcement.
    
    Aggregates traces, timings, and decision logs for debugging.
    """
    
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
        self.timings: Dict[str, float] = {}
        self.decisions: List[Dict[str, Any]] = []
        self.enabled = False
    
    def enable(self) -> None:
        """Enable diagnostic collection."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable diagnostic collection."""
        self.enabled = False
    
    def record_trace(
        self,
        phase: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record trace message.
        
        Args:
            phase: Pipeline phase
            message: Trace message
            metadata: Optional metadata
        """
        if not self.enabled:
            return
        
        self.traces.append({
            'phase': phase,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': metadata or {}
        })
    
    def record_timing(
        self,
        operation: str,
        duration_ms: float
    ) -> None:
        """
        Record operation timing.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
        """
        if not self.enabled:
            return
        
        if operation in self.timings:
            self.timings[operation] += duration_ms
        else:
            self.timings[operation] = duration_ms
    
    def record_decision(
        self,
        clause_id: str,
        decision: bool,
        reason: str
    ) -> None:
        """
        Record validation decision.
        
        Args:
            clause_id: Clause identifier
            decision: Validation result
            reason: Decision reason
        """
        if not self.enabled:
            return
        
        self.decisions.append({
            'clause_id': clause_id,
            'decision': 'pass' if decision else 'fail',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    def get_report(self) -> Dict[str, Any]:
        """Get diagnostic report."""
        return {
            'traces': self.traces,
            'timings': self.timings,
            'decisions': self.decisions,
            'total_traces': len(self.traces),
            'total_operations': len(self.timings),
            'total_time_ms': sum(self.timings.values())
        }
    
    def clear(self) -> None:
        """Clear all collected diagnostics."""
        self.traces.clear()
        self.timings.clear()
        self.decisions.clear()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 60: PYTHON INVOCATION PIPELINE
# ════════════════════════════════════════════════════════════════════════════

class PythonInvocationPipeline:
    """
    Complete Python FFI invocation pipeline.
    
    Orchestrates normalization, validation, invocation, and cleanup
    with full diagnostic and exception support.
    """
    
    def __init__(
        self,
        adapter: 'PythonAdapter'
    ):
        """
        Initialize pipeline.
        
        Args:
            adapter: PythonAdapter instance
        """
        self.adapter = adapter
        self.diagnostics = DiagnosticCollector()
    
    def execute(
        self,
        function_name: str,
        inputs: List[Any],
        native_callable: Optional[Callable] = None
    ) -> Any:
        """
        Execute complete invocation pipeline.
        
        Args:
            function_name: Function name
            inputs: Input arguments
            native_callable: Optional native callable (for testing)
            
        Returns:
            Function result
            
        Raises:
            ContractViolationError: If validation fails
            NativeCrashError: If native code crashes
        """
        start_time = datetime.utcnow()
        
        # Create enforcement context
        context = self.adapter.create_enforcement_context(function_name)
        
        self.diagnostics.record_trace(
            'setup',
            f'Starting invocation of {function_name}',
            {'input_count': len(inputs)}
        )
        
        try:
            # Phase 1: Normalization
            norm_start = datetime.utcnow()
            normalized = self.adapter.normalizer.normalize_inputs(inputs)
            norm_duration = (
                (datetime.utcnow() - norm_start).total_seconds() * 1000
            )
            
            self.diagnostics.record_timing('normalization', norm_duration)
            self.diagnostics.record_trace(
                'normalization',
                f'Normalized {len(inputs)} inputs',
                {'duration_ms': norm_duration}
            )
            
            # Phase 2: Buffer pinning
            pin_start = datetime.utcnow()
            for inp in inputs:
                if isinstance(inp, (bytes, bytearray, memoryview)):
                    self.adapter.memory_manager.wrap_buffer(inp)
            pin_duration = (
                (datetime.utcnow() - pin_start).total_seconds() * 1000
            )
            
            self.diagnostics.record_timing('buffer_pinning', pin_duration)
            
            # Phase 3: Pre-call validation
            graph = self.adapter.get_validation_graph(function_name)
            if graph:
                val_start = datetime.utcnow()
                valid = self.adapter.validation_engine.validate(
                    graph, normalized, context
                )
                val_duration = (
                    (datetime.utcnow() - val_start).total_seconds() * 1000
                )
                
                self.diagnostics.record_timing('validation', val_duration)
                
                if not valid:
                    # Find the failing validation result
                    for result in context.validation_results:
                        if result['status'] == 'fail':
                            report = ViolationReport(
                                function_name,
                                result['clause_id'],
                                'unknown',
                                ClauseSeverity.MANDATORY,
                                'validation pass',
                                'validation fail',
                                result.get('message', ''),
                                self.adapter.contract_fingerprint or '',
                                result['timestamp']
                            )
                            raise (
                                self.adapter.exception_translator
                                .translate_violation(report, context)
                            )
            
            # Phase 4: Native invocation
            if native_callable:
                invoke_start = datetime.utcnow()
                result = native_callable(*normalized)
                invoke_duration = (
                    (datetime.utcnow() - invoke_start).total_seconds() * 1000
                )
                self.diagnostics.record_timing('invocation', invoke_duration)
            else:
                result = None
            
            # Phase 5: Cleanup
            self.adapter.memory_manager.cleanup()
            
            total_duration = (
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            self.diagnostics.record_timing('total', total_duration)
            
            context.finalize()
            
            return result
            
        except Exception as e:
            # Record exception
            self.diagnostics.record_trace(
                'exception',
                f'Exception during invocation: {type(e).__name__}',
                {'message': str(e)}
            )
            
            # Cleanup on error
            try:
                self.adapter.memory_manager.cleanup()
            except Exception:
                pass
            
            raise


# ════════════════════════════════════════════════════════════════════════════
# SECTION 61: COMPLETE PYTHON ADAPTER
# ════════════════════════════════════════════════════════════════════════════

class PythonAdapterComplete(PythonAdapter):
    """
    Complete, production-ready Python FFI adapter.
    
    Integrates all Python specialization components with full
    enforcement pipeline, diagnostics, and exception handling.
    """
    
    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        ffi_mode: str = 'ctypes'
    ):
        """
        Initialize complete Python adapter.
        
        Args:
            config: Adapter configuration
            ffi_mode: FFI mechanism ('ctypes' or 'cffi')
        """
        super().__init__(config, ffi_mode)
        
        # Initialize pipeline
        self.pipeline = PythonInvocationPipeline(self)
        
        # Configuration flags
        self.enable_diagnostics = False
    
    def enable_diagnostic_mode(self) -> None:
        """Enable diagnostic collection."""
        self.enable_diagnostics = True
        self.pipeline.diagnostics.enable()
    
    def disable_diagnostic_mode(self) -> None:
        """Disable diagnostic collection."""
        self.enable_diagnostics = False
        self.pipeline.diagnostics.disable()
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get collected diagnostics."""
        return self.pipeline.diagnostics.get_report()
    
    def clear_diagnostics(self) -> None:
        """Clear diagnostic history."""
        self.pipeline.diagnostics.clear()
    
    def enforcement_scope(
        self,
        function_name: str
    ) -> EnforcementScope:
        """
        Create enforcement scope for function.
        
        Args:
            function_name: Function name
            
        Returns:
            EnforcementScope context manager
        """
        return EnforcementScope(self, function_name)
    
    def call_with_enforcement(
        self,
        function_name: str,
        *args,
        native_callable: Optional[Callable] = None
    ) -> Any:
        """
        Call function with full enforcement pipeline.
        
        Args:
            function_name: Function name
            *args: Function arguments
            native_callable: Optional native callable
            
        Returns:
            Function result
            
        Raises:
            ContractViolationError: If validation fails
            NativeCrashError: If native crashes
        """
        return self.pipeline.execute(
            function_name,
            list(args),
            native_callable
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get adapter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'loaded_functions': len(self.validation_graphs),
            'ffi_mode': self.ffi_mode,
            'diagnostics_enabled': self.enable_diagnostics,
            'memory_stats': self.memory_manager.get_statistics()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        diag = self.get_diagnostics()
        
        return {
            'total_invocations': diag.get('total_operations', 0),
            'total_time_ms': diag.get('total_time_ms', 0),
            'average_time_ms': (
                diag.get('total_time_ms', 0) /
                max(1, diag.get('total_operations', 1))
            ),
            'timing_breakdown': diag.get('timings', {}),
            'memory_stats': self.memory_manager.get_statistics()
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 62: OWNERSHIP STATES EXTENDED
# ════════════════════════════════════════════════════════════════════════════

class OwnershipStateExtended(Enum):
    """Extended ownership states for lifecycle tracking."""
    ALLOCATED = "allocated"
    IN_CALL = "in_call"
    BORROWED = "borrowed"
    TRANSFERRED = "transferred"
    RETURNED = "returned"
    FREED = "freed"
    SHARED = "shared"


# ════════════════════════════════════════════════════════════════════════════
# SECTION 63: TRANSFER ANNOTATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class TransferAnnotation:
    """
    Ownership transfer annotation from contract.
    
    Specifies how ownership transfers during FFI call.
    """
    
    parameter_index: int
    transfer_kind: str  # 'transfer', 'borrow', 'shared'
    direction: str  # 'caller_to_callee', 'callee_to_caller'
    condition: str = 'always'  # 'always', 'on_success', 'on_failure'
    free_function: Optional[str] = None
    
    def should_transfer(self, call_succeeded: bool) -> bool:
        """
        Check if ownership should transfer based on call result.
        
        Args:
            call_succeeded: Whether call succeeded
            
        Returns:
            True if ownership should transfer
        """
        if self.condition == 'always':
            return True
        elif self.condition == 'on_success':
            return call_succeeded
        elif self.condition == 'on_failure':
            return not call_succeeded
        else:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'parameter_index': self.parameter_index,
            'transfer_kind': self.transfer_kind,
            'direction': self.direction,
            'condition': self.condition,
            'free_function': self.free_function
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 64: OWNERSHIP GRAPH
# ════════════════════════════════════════════════════════════════════════════

class OwnershipGraph:
    """
    Graph-based ownership tracking.
    
    Tracks memory allocations and ownership relationships using
    directed graph structure.
    """
    
    def __init__(self):
        # Nodes: address -> allocation info
        self.allocations: Dict[int, Dict[str, Any]] = {}
        
        # Edges: address -> owner identifier
        self.ownership_edges: Dict[int, str] = {}
        
        # Reference counts for shared ownership
        self.ref_counts: Dict[int, int] = {}
        
        # Lifecycle hooks
        self.hooks: Dict[str, List[Callable]] = {
            'on_allocate': [],
            'on_transfer': [],
            'on_borrow': [],
            'on_return': [],
            'on_free': []
        }
    
    def add_allocation(
        self,
        address: int,
        size: int,
        owner: str,
        state: OwnershipStateExtended = OwnershipStateExtended.ALLOCATED
    ) -> None:
        """
        Add allocation to graph.
        
        Args:
            address: Memory address
            size: Allocation size
            owner: Initial owner
            state: Initial ownership state
        """
        self.allocations[address] = {
            'address': address,
            'size': size,
            'state': state,
            'allocated_at': datetime.utcnow().isoformat() + 'Z',
            'history': []
        }
        
        self.ownership_edges[address] = owner
        self.ref_counts[address] = 1
        
        # Trigger hooks
        self._trigger_hooks('on_allocate', address, size, owner)
    
    def transfer_ownership(
        self,
        address: int,
        new_owner: str
    ) -> None:
        """
        Transfer ownership to new owner.
        
        Args:
            address: Memory address
            new_owner: New owner identifier
            
        Raises:
            ValueError: If allocation not found or invalid state
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        alloc = self.allocations[address]
        
        if alloc['state'] == OwnershipStateExtended.FREED:
            raise ValueError(
                f"Cannot transfer freed allocation: {hex(address)}"
            )
        
        old_owner = self.ownership_edges[address]
        
        # Update state
        alloc['state'] = OwnershipStateExtended.TRANSFERRED
        alloc['history'].append({
            'event': 'transfer',
            'from': old_owner,
            'to': new_owner,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Update edge
        self.ownership_edges[address] = new_owner
        
        # Trigger hooks
        self._trigger_hooks('on_transfer', address, old_owner, new_owner)
    
    def borrow_allocation(
        self,
        address: int,
        borrower: str
    ) -> None:
        """
        Mark allocation as borrowed.
        
        Args:
            address: Memory address
            borrower: Borrower identifier
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        alloc = self.allocations[address]
        alloc['state'] = OwnershipStateExtended.BORROWED
        alloc['history'].append({
            'event': 'borrow',
            'borrower': borrower,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Trigger hooks
        self._trigger_hooks('on_borrow', address, borrower)
    
    def return_allocation(
        self,
        address: int
    ) -> None:
        """
        Mark borrowed allocation as returned.
        
        Args:
            address: Memory address
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        alloc = self.allocations[address]
        
        if alloc['state'] != OwnershipStateExtended.BORROWED:
            raise ValueError(
                f"Allocation not borrowed: {hex(address)}"
            )
        
        alloc['state'] = OwnershipStateExtended.RETURNED
        alloc['history'].append({
            'event': 'return',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        owner = self.ownership_edges[address]
        
        # Trigger hooks
        self._trigger_hooks('on_return', address, owner)
    
    def add_reference(
        self,
        address: int
    ) -> None:
        """
        Increment reference count for shared ownership.
        
        Args:
            address: Memory address
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        self.ref_counts[address] += 1
        self.allocations[address]['state'] = OwnershipStateExtended.SHARED
    
    def remove_reference(
        self,
        address: int
    ) -> bool:
        """
        Decrement reference count.
        
        Args:
            address: Memory address
            
        Returns:
            True if reference count reached zero (should free)
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        self.ref_counts[address] -= 1
        
        if self.ref_counts[address] <= 0:
            return True
        
        return False
    
    def mark_freed(
        self,
        address: int
    ) -> None:
        """
        Mark allocation as freed.
        
        Args:
            address: Memory address
        """
        if address not in self.allocations:
            raise ValueError(f"Unknown allocation: {hex(address)}")
        
        alloc = self.allocations[address]
        
        if alloc['state'] == OwnershipStateExtended.FREED:
            raise ValueError(f"Double-free: {hex(address)}")
        
        alloc['state'] = OwnershipStateExtended.FREED
        alloc['freed_at'] = datetime.utcnow().isoformat() + 'Z'
        
        owner = self.ownership_edges[address]
        
        # Trigger hooks
        self._trigger_hooks('on_free', address, owner)
    
    def get_owner(self, address: int) -> Optional[str]:
        """Get current owner of allocation."""
        return self.ownership_edges.get(address)
    
    def get_state(
        self, address: int
    ) -> Optional[OwnershipStateExtended]:
        """Get current state of allocation."""
        if address in self.allocations:
            return self.allocations[address]['state']
        return None
    
    def register_hook(
        self,
        hook_name: str,
        callback: Callable
    ) -> None:
        """
        Register lifecycle hook.
        
        Args:
            hook_name: Hook name (on_allocate, on_transfer, etc.)
            callback: Hook callback function
        """
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)
    
    def _trigger_hooks(
        self,
        hook_name: str,
        *args
    ) -> None:
        """Trigger lifecycle hooks."""
        for callback in self.hooks.get(hook_name, []):
            try:
                callback(*args)
            except Exception:
                pass  # Don't let hook errors break ownership tracking


# ════════════════════════════════════════════════════════════════════════════
# SECTION 65: OWNERSHIP STATE MACHINE
# ════════════════════════════════════════════════════════════════════════════

class OwnershipStateMachine:
    """
    Validates ownership state transitions.
    
    Ensures state transitions follow valid patterns.
    """
    
    # Valid transitions: current_state -> allowed_next_states
    VALID_TRANSITIONS: Dict[
        OwnershipStateExtended, set
    ] = {
        OwnershipStateExtended.ALLOCATED: {
            OwnershipStateExtended.IN_CALL,
            OwnershipStateExtended.BORROWED,
            OwnershipStateExtended.TRANSFERRED,
            OwnershipStateExtended.SHARED,
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.IN_CALL: {
            OwnershipStateExtended.RETURNED,
            OwnershipStateExtended.TRANSFERRED,
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.BORROWED: {
            OwnershipStateExtended.RETURNED,
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.TRANSFERRED: {
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.RETURNED: {
            OwnershipStateExtended.IN_CALL,
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.SHARED: {
            OwnershipStateExtended.FREED
        },
        OwnershipStateExtended.FREED: set()  # Terminal state
    }
    
    def is_valid_transition(
        self,
        current_state: OwnershipStateExtended,
        next_state: OwnershipStateExtended
    ) -> bool:
        """
        Check if state transition is valid.
        
        Args:
            current_state: Current ownership state
            next_state: Proposed next state
            
        Returns:
            True if transition is valid
        """
        allowed = self.VALID_TRANSITIONS.get(current_state, set())
        return next_state in allowed
    
    def validate_transition(
        self,
        current_state: OwnershipStateExtended,
        next_state: OwnershipStateExtended
    ) -> None:
        """
        Validate state transition, raise if invalid.
        
        Args:
            current_state: Current ownership state
            next_state: Proposed next state
            
        Raises:
            ValueError: If transition is invalid
        """
        if not self.is_valid_transition(current_state, next_state):
            raise ValueError(
                f"Invalid ownership transition: "
                f"{current_state.value} -> {next_state.value}"
            )


# ════════════════════════════════════════════════════════════════════════════
# SECTION 66: TRANSFER SEMANTICS
# ════════════════════════════════════════════════════════════════════════════

class TransferSemantics:
    """
    Implements ownership transfer semantics.
    
    Applies transfer annotations to ownership graph during FFI calls.
    """
    
    def __init__(self, ownership_graph: OwnershipGraph):
        self.graph = ownership_graph
        self.state_machine = OwnershipStateMachine()
    
    def apply_pre_call_transfers(
        self,
        annotations: List[TransferAnnotation],
        addresses: Dict[int, int]
    ) -> None:
        """
        Apply ownership transfers before native call.
        
        Args:
            annotations: Transfer annotations
            addresses: Parameter index -> memory address mapping
        """
        for annotation in annotations:
            if annotation.direction != 'caller_to_callee':
                continue
            
            address = addresses.get(annotation.parameter_index)
            if address is None:
                continue
            
            if annotation.transfer_kind == 'transfer':
                self.graph.transfer_ownership(address, 'callee')
            elif annotation.transfer_kind == 'borrow':
                self.graph.borrow_allocation(address, 'callee')
            elif annotation.transfer_kind == 'shared':
                self.graph.add_reference(address)
    
    def apply_post_call_transfers(
        self,
        annotations: List[TransferAnnotation],
        addresses: Dict[int, int],
        call_succeeded: bool
    ) -> None:
        """
        Apply ownership transfers after native call.
        
        Args:
            annotations: Transfer annotations
            addresses: Parameter index -> memory address mapping
            call_succeeded: Whether call succeeded
        """
        for annotation in annotations:
            address = addresses.get(annotation.parameter_index)
            if address is None:
                continue
            
            # Check if transfer should occur
            if not annotation.should_transfer(call_succeeded):
                continue
            
            # Handle borrow returns
            if annotation.transfer_kind == 'borrow':
                current_state = self.graph.get_state(address)
                if current_state == OwnershipStateExtended.BORROWED:
                    self.graph.return_allocation(address)
            
            # Handle callee-to-caller transfers
            if annotation.direction == 'callee_to_caller':
                if annotation.transfer_kind == 'transfer':
                    self.graph.transfer_ownership(address, 'caller')


# ════════════════════════════════════════════════════════════════════════════
# SECTION 67: OWNERSHIP VALIDATOR
# ════════════════════════════════════════════════════════════════════════════

class OwnershipValidator:
    """
    Validates ownership operations for safety.
    
    Checks operations against ownership state before allowing them.
    """
    
    def __init__(self, ownership_graph: OwnershipGraph):
        self.graph = ownership_graph
        self.state_machine = OwnershipStateMachine()
    
    def can_free(
        self,
        address: int,
        requester: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if requester can free allocation.
        
        Args:
            address: Memory address
            requester: Requester identifier
            
        Returns:
            Tuple of (can_free, error_message)
        """
        owner = self.graph.get_owner(address)
        if owner != requester:
            return (
                False,
                f"Only owner can free: owner={owner}, "
                f"requester={requester}"
            )
        
        state = self.graph.get_state(address)
        if state == OwnershipStateExtended.FREED:
            return (False, "Allocation already freed")
        
        if state == OwnershipStateExtended.BORROWED:
            return (False, "Cannot free while borrowed")
        
        return (True, None)
    
    def can_transfer(
        self,
        address: int,
        requester: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if requester can transfer allocation.
        
        Args:
            address: Memory address
            requester: Requester identifier
            
        Returns:
            Tuple of (can_transfer, error_message)
        """
        owner = self.graph.get_owner(address)
        if owner != requester:
            return (
                False,
                f"Only owner can transfer: owner={owner}, "
                f"requester={requester}"
            )
        
        state = self.graph.get_state(address)
        if state == OwnershipStateExtended.FREED:
            return (False, "Cannot transfer freed allocation")
        
        return (True, None)
    
    def can_access(
        self,
        address: int,
        requester: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if requester can access allocation.
        
        Args:
            address: Memory address
            requester: Requester identifier
            
        Returns:
            Tuple of (can_access, error_message)
        """
        state = self.graph.get_state(address)
        
        if state == OwnershipStateExtended.FREED:
            return (False, "Cannot access freed allocation")
        
        owner = self.graph.get_owner(address)
        
        # Owner can always access
        if owner == requester:
            return (True, None)
        
        # Borrower can access while borrowed
        if state == OwnershipStateExtended.BORROWED:
            return (True, None)
        
        # Shared allocations can be accessed
        if state == OwnershipStateExtended.SHARED:
            return (True, None)
        
        return (False, "Access denied: not owner or borrower")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 68: CONTRACT METADATA
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ContractMetadata:
    """
    Rich metadata about contract.
    
    Contains documentation, versioning, and auxiliary information
    beyond validation rules.
    """
    
    contract_id: str
    version: str = "1.0.0"
    author: Optional[str] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    source_file: Optional[str] = None
    
    # Function metadata
    function_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Platform compatibility
    supported_platforms: List[str] = field(default_factory=list)
    min_language_version: Optional[str] = None
    
    # Performance hints
    performance_hints: Dict[str, Any] = field(default_factory=dict)
    
    # Security metadata
    security_level: str = "standard"
    requires_encryption: bool = False
    
    def get_function_metadata(
        self,
        function_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for specific function.
        
        Args:
            function_name: Function name
            
        Returns:
            Function metadata or None
        """
        return self.function_metadata.get(function_name)
    
    def add_function_metadata(
        self,
        function_name: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Add metadata for function.
        
        Args:
            function_name: Function name
            metadata: Function metadata
        """
        self.function_metadata[function_name] = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'contract_id': self.contract_id,
            'version': self.version,
            'author': self.author,
            'created_at': self.created_at,
            'description': self.description,
            'source_file': self.source_file,
            'function_metadata': self.function_metadata,
            'supported_platforms': self.supported_platforms,
            'min_language_version': self.min_language_version,
            'performance_hints': self.performance_hints,
            'security_level': self.security_level,
            'requires_encryption': self.requires_encryption
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 69: STATE SNAPSHOT
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class StateSnapshot:
    """
    Point-in-time snapshot of adapter state.
    
    Captures complete state for debugging and analysis.
    """
    
    timestamp: str
    active_invocations: List[Dict[str, Any]] = field(default_factory=list)
    ownership_state: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    loaded_functions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'active_invocations': self.active_invocations,
            'ownership_state': self.ownership_state,
            'configuration': self.configuration,
            'statistics': self.statistics,
            'loaded_functions': self.loaded_functions
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 70: HISTORY TRACKER
# ════════════════════════════════════════════════════════════════════════════

class HistoryTracker:
    """
    Tracks invocation history.
    
    Records past invocations, violations, and state changes for analysis.
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.invocations: List[Dict[str, Any]] = []
        self.violations: List[Dict[str, Any]] = []
        self.state_changes: List[Dict[str, Any]] = []
    
    def record_invocation(
        self,
        function_name: str,
        success: bool,
        duration_ms: float,
        context: Optional[EnforcementContext] = None
    ) -> None:
        """
        Record invocation.
        
        Args:
            function_name: Function name
            success: Whether invocation succeeded
            duration_ms: Execution duration
            context: Enforcement context
        """
        self.invocations.append({
            'function_name': function_name,
            'success': success,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'context_id': context.invocation_id if context else None
        })
        
        # Limit history size
        if len(self.invocations) > self.max_history:
            self.invocations.pop(0)
    
    def record_violation(
        self,
        function_name: str,
        clause_id: str,
        message: str
    ) -> None:
        """
        Record contract violation.
        
        Args:
            function_name: Function name
            clause_id: Violated clause
            message: Violation message
        """
        self.violations.append({
            'function_name': function_name,
            'clause_id': clause_id,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        if len(self.violations) > self.max_history:
            self.violations.pop(0)
    
    def record_state_change(
        self,
        change_type: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Record state change.
        
        Args:
            change_type: Type of change
            details: Change details
        """
        self.state_changes.append({
            'change_type': change_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        if len(self.state_changes) > self.max_history:
            self.state_changes.pop(0)
    
    def get_recent_invocations(
        self,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent invocations."""
        return self.invocations[-count:]
    
    def get_recent_violations(
        self,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent violations."""
        return self.violations[-count:]
    
    def get_invocation_statistics(self) -> Dict[str, Any]:
        """Get invocation statistics."""
        total = len(self.invocations)
        if total == 0:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        successful = len([i for i in self.invocations if i['success']])
        
        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'average_duration_ms': sum(
                i['duration_ms'] for i in self.invocations
            ) / total
        }
    
    def clear_history(self) -> None:
        """Clear all history."""
        self.invocations.clear()
        self.violations.clear()
        self.state_changes.clear()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 71: QUERY ENGINE
# ════════════════════════════════════════════════════════════════════════════

class QueryEngine:
    """
    Structured query interface for adapter introspection.
    
    Supports dot-notation queries to access adapter state and metadata.
    """
    
    def __init__(self, adapter: 'LanguageAdapter'):
        self.adapter = adapter
    
    def query(self, query_path: str) -> Any:
        """
        Execute query using dot notation.
        
        Args:
            query_path: Query path (e.g., 'contract.functions')
            
        Returns:
            Query result
            
        Raises:
            ValueError: If query path is invalid
        """
        parts = query_path.split('.')
        
        if not parts or parts == ['']:
            raise ValueError("Empty query path")
        
        # Route to appropriate handler
        if parts[0] == 'contract':
            return self._query_contract(parts[1:])
        elif parts[0] == 'state':
            return self._query_state(parts[1:])
        elif parts[0] == 'stats':
            return self._query_statistics(parts[1:])
        elif parts[0] == 'config':
            return self._query_configuration(parts[1:])
        else:
            raise ValueError(f"Unknown query root: {parts[0]}")
    
    def _query_contract(self, path: List[str]) -> Any:
        """Query contract information."""
        if not path:
            # Return all contract info
            return {
                'fingerprint': self.adapter.contract_fingerprint,
                'functions': list(self.adapter.validation_graphs.keys())
            }
        
        if path[0] == 'functions':
            return list(self.adapter.validation_graphs.keys())
        
        if path[0] == 'function' and len(path) >= 2:
            func_name = path[1]
            graph = self.adapter.get_validation_graph(func_name)
            
            if not graph:
                return None
            
            if len(path) == 2:
                return {
                    'name': func_name,
                    'clauses': len(graph.nodes),
                    'clause_ids': [n.clause_id for n in graph.nodes]
                }
            
            if path[2] == 'parameters':
                return [n.parameters for n in graph.nodes]
        
        return None
    
    def _query_state(self, path: List[str]) -> Any:
        """Query runtime state."""
        if not path:
            return {
                'has_contract': self.adapter.contract_fingerprint is not None,
                'loaded_functions': len(self.adapter.validation_graphs)
            }
        
        if path[0] == 'ownership' and len(path) >= 2:
            if path[1] == 'allocations':
                return self.adapter.ownership_registry.get_statistics()
        
        return None
    
    def _query_statistics(self, path: List[str]) -> Any:
        """Query statistics."""
        # Build stats from adapter state
        stats = {
            'loaded_functions': len(self.adapter.validation_graphs),
            'contract_loaded': self.adapter.contract_fingerprint is not None
        }
        
        # Use get_statistics if available (e.g. PythonAdapterComplete)
        if hasattr(self.adapter, 'get_statistics'):
            stats.update(self.adapter.get_statistics())
        
        if not path:
            return stats
        
        # Navigate path
        current = stats
        for part in path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _query_configuration(self, path: List[str]) -> Any:
        """Query configuration."""
        if hasattr(self.adapter, 'config') and self.adapter.config:
            config_dict = self.adapter.config.to_dict()
            
            if not path:
                return config_dict
            
            current = config_dict
            for part in path:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            
            return current
        
        return None


# ════════════════════════════════════════════════════════════════════════════
# SECTION 72: METADATA ENRICHER
# ════════════════════════════════════════════════════════════════════════════

class MetadataEnricher:
    """
    Enriches runtime data with contract metadata.
    
    Adds context and documentation to errors, diagnostics, and reports.
    """
    
    def __init__(self, contract_metadata: Optional[ContractMetadata] = None):
        self.metadata = contract_metadata
    
    def enrich_violation_report(
        self,
        report: ViolationReport
    ) -> Dict[str, Any]:
        """
        Enrich violation report with metadata.
        
        Args:
            report: Violation report
            
        Returns:
            Enriched report dictionary
        """
        enriched = report.to_dict()
        
        if self.metadata:
            func_metadata = self.metadata.get_function_metadata(
                report.function_name
            )
            
            if func_metadata:
                enriched['function_description'] = func_metadata.get(
                    'description'
                )
                enriched['documentation_url'] = func_metadata.get(
                    'docs_url'
                )
        
        return enriched
    
    def enrich_enforcement_context(
        self,
        context: EnforcementContext
    ) -> Dict[str, Any]:
        """
        Enrich enforcement context with metadata.
        
        Args:
            context: Enforcement context
            
        Returns:
            Enriched context dictionary
        """
        enriched = context.to_dict()
        
        if self.metadata:
            func_metadata = self.metadata.get_function_metadata(
                context.function_name
            )
            
            if func_metadata:
                enriched['metadata'] = {
                    'description': func_metadata.get('description'),
                    'expected_frequency': func_metadata.get(
                        'call_frequency'
                    ),
                    'performance_hint': func_metadata.get(
                        'performance_hint'
                    )
                }
        
        return enriched


# ════════════════════════════════════════════════════════════════════════════
# SECTION 73: INTROSPECTION API
# ════════════════════════════════════════════════════════════════════════════

class IntrospectionAPI:
    """
    High-level introspection API.
    
    Provides convenient methods for common introspection tasks.
    """
    
    def __init__(self, adapter: 'LanguageAdapter'):
        self.adapter = adapter
        self.query_engine = QueryEngine(adapter)
        self.history_tracker = HistoryTracker()
        self.metadata: Optional[ContractMetadata] = None
        self.enricher = MetadataEnricher()
    
    def set_metadata(self, metadata: ContractMetadata) -> None:
        """Set contract metadata."""
        self.metadata = metadata
        self.enricher = MetadataEnricher(metadata)
    
    def get_loaded_functions(self) -> List[str]:
        """Get list of loaded functions."""
        return self.query_engine.query('contract.functions')
    
    def get_function_info(
        self,
        function_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get information about function."""
        return self.query_engine.query(
            f'contract.function.{function_name}'
        )
    
    def get_ownership_statistics(self) -> Dict[str, Any]:
        """Get ownership tracking statistics."""
        return self.query_engine.query('state.ownership.allocations')
    
    def create_snapshot(self) -> StateSnapshot:
        """
        Create state snapshot.
        
        Returns:
            StateSnapshot of current state
        """
        snapshot = StateSnapshot(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            ownership_state=self.get_ownership_statistics() or {},
            configuration=self.query_engine.query('config') or {},
            statistics=self.query_engine.query('stats') or {},
            loaded_functions=self.get_loaded_functions()
        )
        
        return snapshot
    
    def get_recent_invocations(
        self,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent invocations."""
        return self.history_tracker.get_recent_invocations(count)
    
    def get_recent_violations(
        self,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent violations."""
        return self.history_tracker.get_recent_violations(count)
    
    def get_invocation_statistics(self) -> Dict[str, Any]:
        """Get invocation statistics from history."""
        return self.history_tracker.get_invocation_statistics()
    
    def query(self, query_path: str) -> Any:
        """Execute arbitrary query."""
        return self.query_engine.query(query_path)
