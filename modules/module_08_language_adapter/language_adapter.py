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
        
        return {
            'valid': result['valid'],
            'context': context.to_dict(),
            'metrics': result
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'config': self.config.to_dict(),
            'contract_fingerprint': self.contract_fingerprint,
            'loaded_functions': len(self.validation_graphs),
            'ownership': self.ownership_registry.get_statistics()
        }
