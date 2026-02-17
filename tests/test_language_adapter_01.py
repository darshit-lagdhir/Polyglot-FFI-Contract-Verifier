"""
Test Suite for Language Adapter - Prompt 01/25 (Parts A+B)
Foundation: Core Data Structures, Projection, and Registry

Tests cover:
- ValidationNode creation and operations (20 tests)
- ValidationGraph construction and topological sort (25 tests)
- OwnershipState transitions and validation (15 tests)
- EnforcementContext tracking (15 tests)
- ViolationReport structure (15 tests)
- ContractProjector loading (15 tests)
- OwnershipRegistry tracking (10 tests)
- LanguageAdapter coordination (5 tests)

Total: 120 tests (HARD level - comprehensive coverage)
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from modules.module_08_language_adapter import (
    ClauseSeverity,
    OwnershipKind,
    ValidationStatus,
    EnforcementMode,
    ValidationNode,
    ValidationGraph,
    OwnershipState,
    EnforcementContext,
    ViolationReport,
    ContractProjector,
    OwnershipRegistry,
    AdapterConfig,
    LanguageAdapter,
)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1: ValidationNode Tests (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestValidationNode:
    """Test ValidationNode data structure."""
    
    def test_create_basic_node(self):
        """Test 1: Create basic validation node."""
        node = ValidationNode(
            clause_id='test_clause_1',
            clause_type='range_check',
            severity=ClauseSeverity.MANDATORY
        )
        assert node.clause_id == 'test_clause_1'
        assert node.clause_type == 'range_check'
        assert node.severity == ClauseSeverity.MANDATORY
    
    def test_node_with_parameters(self):
        """Test 2: Node with parameter references."""
        node = ValidationNode(
            clause_id='param_check',
            clause_type='nullability',
            severity=ClauseSeverity.MANDATORY,
            parameters=[0, 1]
        )
        assert node.parameters == [0, 1]
        assert len(node.parameters) == 2
    
    def test_node_with_predicate(self):
        """Test 3: Node with validation predicate."""
        def check_positive(inputs, params):
            return inputs[params[0]] > 0
        
        node = ValidationNode(
            clause_id='positive_check',
            clause_type='range',
            severity=ClauseSeverity.MANDATORY,
            predicate=check_positive,
            parameters=[0]
        )
        assert node.predicate([5], [0]) is True
        assert node.predicate([-5], [0]) is False
    
    def test_node_failure_message(self):
        """Test 4: Custom failure message."""
        msg = 'Value must be in range [0, 100]'
        node = ValidationNode(
            clause_id='range',
            clause_type='range',
            severity=ClauseSeverity.MANDATORY,
            failure_message=msg
        )
        assert node.failure_message == msg
    
    def test_node_metadata(self):
        """Test 5: Node metadata storage."""
        metadata = {'source': 'manual', 'priority': 'high'}
        node = ValidationNode(
            clause_id='custom',
            clause_type='custom',
            severity=ClauseSeverity.ADVISORY,
            metadata=metadata
        )
        assert node.metadata['source'] == 'manual'
        assert node.metadata['priority'] == 'high'
    
    def test_node_hashable(self):
        """Test 6: Nodes are hashable."""
        node1 = ValidationNode('id1', 'type1', ClauseSeverity.MANDATORY)
        node2 = ValidationNode('id1', 'type1', ClauseSeverity.MANDATORY)
        node3 = ValidationNode('id2', 'type1', ClauseSeverity.MANDATORY)
        
        assert hash(node1) == hash(node2)
        assert hash(node1) != hash(node3)
    
    def test_node_equality(self):
        """Test 7: Node equality comparison."""
        node1 = ValidationNode('id1', 'type1', ClauseSeverity.MANDATORY)
        node2 = ValidationNode('id1', 'type1', ClauseSeverity.ADVISORY)
        node3 = ValidationNode('id2', 'type1', ClauseSeverity.MANDATORY)
        
        assert node1 == node2  # Same id and type
        assert node1 != node3  # Different id
    
    def test_node_to_dict(self):
        """Test 8: Node serialization to dict."""
        node = ValidationNode(
            clause_id='serialize',
            clause_type='test',
            severity=ClauseSeverity.MANDATORY,
            parameters=[0, 1],
            failure_message='Test failure'
        )
        data = node.to_dict()
        
        assert data['clause_id'] == 'serialize'
        assert data['clause_type'] == 'test'
        assert data['severity'] == 'mandatory'
        assert data['parameters'] == [0, 1]
        assert data['failure_message'] == 'Test failure'
    
    def test_severity_mandatory(self):
        """Test 9: Mandatory severity."""
        node = ValidationNode('m', 'test', ClauseSeverity.MANDATORY)
        assert node.severity == ClauseSeverity.MANDATORY
        assert node.severity.value == 'mandatory'
    
    def test_severity_advisory(self):
        """Test 10: Advisory severity."""
        node = ValidationNode('a', 'test', ClauseSeverity.ADVISORY)
        assert node.severity == ClauseSeverity.ADVISORY
        assert node.severity.value == 'advisory'
    
    def test_severity_optional(self):
        """Test 11: Optional severity."""
        node = ValidationNode('o', 'test', ClauseSeverity.OPTIONAL)
        assert node.severity == ClauseSeverity.OPTIONAL
        assert node.severity.value == 'optional'
    
    def test_node_empty_parameters(self):
        """Test 12: Node with no parameters."""
        node = ValidationNode('id', 'type', ClauseSeverity.MANDATORY)
        assert node.parameters == []
        assert len(node.parameters) == 0
    
    def test_node_multiple_parameters(self):
        """Test 13: Node with multiple parameters."""
        node = ValidationNode(
            'rel', 'relational', ClauseSeverity.MANDATORY,
            parameters=[0, 1, 2, 3]
        )
        assert len(node.parameters) == 4
        assert node.parameters == [0, 1, 2, 3]
    
    def test_node_empty_metadata(self):
        """Test 14: Node with empty metadata."""
        node = ValidationNode('id', 'type', ClauseSeverity.MANDATORY)
        assert node.metadata == {}
        assert len(node.metadata) == 0
    
    def test_node_complex_metadata(self):
        """Test 15: Node with complex metadata."""
        metadata = {
            'range': {'min': 0, 'max': 100},
            'source_location': {'file': 'test.h', 'line': 42}
        }
        node = ValidationNode(
            'id', 'type', ClauseSeverity.MANDATORY, 
            metadata=metadata
        )
        assert node.metadata['range']['max'] == 100
        assert node.metadata['source_location']['line'] == 42
    
    def test_node_predicate_none(self):
        """Test 16: Node with no predicate."""
        node = ValidationNode('id', 'type', ClauseSeverity.MANDATORY)
        assert node.predicate is None
    
    def test_node_predicate_callable(self):
        """Test 17: Predicate is callable."""
        def pred(inputs, params):
            return True
        
        node = ValidationNode(
            'id', 'type', ClauseSeverity.MANDATORY,
            predicate=pred
        )
        assert callable(node.predicate)
        assert node.predicate([], []) is True
    
    def test_node_failure_message_default(self):
        """Test 18: Default failure message is empty."""
        node = ValidationNode('id', 'type', ClauseSeverity.MANDATORY)
        assert node.failure_message == ""
    
    def test_node_in_set(self):
        """Test 19: Nodes can be added to sets."""
        node1 = ValidationNode('id1', 'type', ClauseSeverity.MANDATORY)
        node2 = ValidationNode('id2', 'type', ClauseSeverity.MANDATORY)
        node3 = ValidationNode('id1', 'type', ClauseSeverity.ADVISORY)
        
        nodes = {node1, node2, node3}
        assert len(nodes) == 2  # node1 and node3 are equal
    
    def test_node_to_dict_preserves_metadata(self):
        """Test 20: to_dict preserves all metadata fields."""
        metadata = {'a': 1, 'b': 'two', 'c': [3, 4, 5]}
        node = ValidationNode(
            'id', 'type', ClauseSeverity.MANDATORY,
            metadata=metadata
        )
        data = node.to_dict()
        assert data['metadata'] == metadata


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2: ValidationGraph Tests (25 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestValidationGraph:
    """Test ValidationGraph operations."""
    
    def test_create_empty_graph(self):
        """Test 21: Create empty validation graph."""
        graph = ValidationGraph(function_name='test_func')
        assert graph.function_name == 'test_func'
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_single_node(self):
        """Test 22: Add single node."""
        graph = ValidationGraph(function_name='func')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        
        assert len(graph.nodes) == 1
        assert node in graph.nodes
        assert 'n1' in graph.edges
    
    def test_add_duplicate_node(self):
        """Test 23: Adding duplicate node doesn't duplicate."""
        graph = ValidationGraph(function_name='func')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        graph.add_node(node)
        
        assert len(graph.nodes) == 1
    
    def test_add_edge(self):
        """Test 24: Add dependency edge."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge('n1', 'n2')
        
        assert 'n2' in graph.edges['n1']
    
    def test_add_edge_creates_entry(self):
        """Test 25: Adding edge creates adjacency list entry."""
        graph = ValidationGraph(function_name='func')
        graph.add_edge('source', 'target')
        
        assert 'source' in graph.edges
        assert 'target' in graph.edges['source']
    
    def test_topological_sort_empty(self):
        """Test 26: Topological sort of empty graph."""
        graph = ValidationGraph(function_name='func')
        order = graph.get_execution_order()
        assert len(order) == 0
    
    def test_topological_sort_single(self):
        """Test 27: Topological sort with single node."""
        graph = ValidationGraph(function_name='func')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        
        order = graph.get_execution_order()
        assert len(order) == 1
        assert order[0] == node
    
    def test_topological_sort_linear(self):
        """Test 28: Topological sort of linear chain."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        n3 = ValidationNode('n3', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_edge('n1', 'n2')
        graph.add_edge('n2', 'n3')
        
        order = graph.get_execution_order()
        assert order[0] == n1
        assert order[1] == n2
        assert order[2] == n3
    
    def test_topological_sort_diamond(self):
        """Test 29: Topological sort of diamond dependency."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        n3 = ValidationNode('n3', 'type', ClauseSeverity.MANDATORY)
        n4 = ValidationNode('n4', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_node(n4)
        
        # Diamond: n1 -> n2, n1 -> n3, n2 -> n4, n3 -> n4
        graph.add_edge('n1', 'n2')
        graph.add_edge('n1', 'n3')
        graph.add_edge('n2', 'n4')
        graph.add_edge('n3', 'n4')
        
        order = graph.get_execution_order()
        n1_idx = order.index(n1)
        n2_idx = order.index(n2)
        n3_idx = order.index(n3)
        n4_idx = order.index(n4)
        
        assert n1_idx < n2_idx
        assert n1_idx < n3_idx
        assert n2_idx < n4_idx
        assert n3_idx < n4_idx
    
    def test_graph_to_dict(self):
        """Test 30: Graph serialization."""
        graph = ValidationGraph(function_name='serialize_test')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        
        data = graph.to_dict()
        assert data['function_name'] == 'serialize_test'
        assert len(data['nodes']) == 1
        assert 'edges' in data
    
    def test_multiple_edges_same_source(self):
        """Test 31: Multiple outgoing edges from same node."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        n3 = ValidationNode('n3', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        graph.add_edge('n1', 'n2')
        graph.add_edge('n1', 'n3')
        
        assert len(graph.edges['n1']) == 2
        assert 'n2' in graph.edges['n1']
        assert 'n3' in graph.edges['n1']
    
    def test_no_duplicate_edges(self):
        """Test 32: Duplicate edges not added."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        
        graph.add_edge('n1', 'n2')
        graph.add_edge('n1', 'n2')
        
        assert len(graph.edges['n1']) == 1
    
    def test_complex_graph_sort(self):
        """Test 33: Complex graph topological sort."""
        graph = ValidationGraph(function_name='complex')
        nodes = [
            ValidationNode(f'n{i}', 'type', ClauseSeverity.MANDATORY) 
            for i in range(6)
        ]
        
        for node in nodes:
            graph.add_node(node)
        
        # Complex dependencies
        graph.add_edge('n0', 'n1')
        graph.add_edge('n0', 'n2')
        graph.add_edge('n1', 'n3')
        graph.add_edge('n2', 'n3')
        graph.add_edge('n3', 'n4')
        graph.add_edge('n4', 'n5')
        
        order = graph.get_execution_order()
        assert len(order) == 6
        assert order[0].clause_id == 'n0'
        assert order[-1].clause_id == 'n5'
    
    def test_graph_with_isolated_nodes(self):
        """Test 34: Graph with no edges."""
        graph = ValidationGraph(function_name='isolated')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        
        order = graph.get_execution_order()
        assert len(order) == 2
    
    def test_graph_function_name_preserved(self):
        """Test 35: Function name preserved."""
        name = 'my_special_function'
        graph = ValidationGraph(function_name=name)
        assert graph.function_name == name
    
    def test_graph_nodes_list_ordering(self):
        """Test 36: Nodes maintain insertion order."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        n3 = ValidationNode('n3', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        assert graph.nodes[0] == n1
        assert graph.nodes[1] == n2
        assert graph.nodes[2] == n3
    
    def test_graph_to_dict_with_edges(self):
        """Test 37: Graph with edges serializes correctly."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge('n1', 'n2')
        
        data = graph.to_dict()
        assert 'n1' in data['edges']
        assert 'n2' in data['edges']['n1']
    
    def test_graph_empty_edges_dict_on_creation(self):
        """Test 38: New graph has empty edges dict."""
        graph = ValidationGraph(function_name='func')
        assert graph.edges == {}
    
    def test_node_edge_list_initialized(self):
        """Test 39: Node gets empty edge list on add."""
        graph = ValidationGraph(function_name='func')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        
        assert 'n1' in graph.edges
        assert graph.edges['n1'] == []
    
    def test_topological_sort_deterministic(self):
        """Test 40: Multiple runs produce same ordering."""
        graph = ValidationGraph(function_name='func')
        nodes = [
            ValidationNode(f'n{i}', 'type', ClauseSeverity.MANDATORY)
            for i in range(5)
        ]
        
        for node in nodes:
            graph.add_node(node)
        
        graph.add_edge('n0', 'n4')
        graph.add_edge('n1', 'n4')
        graph.add_edge('n2', 'n4')
        
        order1 = graph.get_execution_order()
        order2 = graph.get_execution_order()
        order3 = graph.get_execution_order()
        
        assert order1 == order2 == order3
    
    def test_graph_multiple_roots(self):
        """Test 41: Graph with multiple root nodes."""
        graph = ValidationGraph(function_name='func')
        n1 = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        n2 = ValidationNode('n2', 'type', ClauseSeverity.MANDATORY)
        n3 = ValidationNode('n3', 'type', ClauseSeverity.MANDATORY)
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        graph.add_edge('n1', 'n3')
        graph.add_edge('n2', 'n3')
        
        order = graph.get_execution_order()
        n3_idx = order.index(n3)
        n1_idx = order.index(n1)
        n2_idx = order.index(n2)
        
        assert n1_idx < n3_idx
        assert n2_idx < n3_idx
    
    def test_to_dict_includes_all_fields(self):
        """Test 42: to_dict includes function_name, nodes, edges."""
        graph = ValidationGraph(function_name='complete')
        node = ValidationNode('n1', 'type', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        graph.add_edge('n1', 'n2')
        
        data = graph.to_dict()
        assert 'function_name' in data
        assert 'nodes' in data
        assert 'edges' in data
    
    def test_add_multiple_nodes_efficiently(self):
        """Test 43: Can add many nodes efficiently."""
        graph = ValidationGraph(function_name='large')
        nodes = [
            ValidationNode(f'n{i}', 'type', ClauseSeverity.MANDATORY)
            for i in range(100)
        ]
        
        for node in nodes:
            graph.add_node(node)
        
        assert len(graph.nodes) == 100
        assert len(graph.edges) == 100
    
    def test_topological_sort_large_graph(self):
        """Test 44: Topological sort works on large graphs."""
        graph = ValidationGraph(function_name='large')
        nodes = [
            ValidationNode(f'n{i}', 'type', ClauseSeverity.MANDATORY)
            for i in range(50)
        ]
        
        for node in nodes:
            graph.add_node(node)
        
        # Create chain
        for i in range(49):
            graph.add_edge(f'n{i}', f'n{i+1}')
        
        order = graph.get_execution_order()
        assert len(order) == 50
        assert order[0].clause_id == 'n0'
        assert order[49].clause_id == 'n49'
    
    def test_graph_preserves_node_types(self):
        """Test 45: Graph preserves different node types."""
        graph = ValidationGraph(function_name='func')
        mandatory = ValidationNode('m', 'type', ClauseSeverity.MANDATORY)
        advisory = ValidationNode('a', 'type', ClauseSeverity.ADVISORY)
        optional = ValidationNode('o', 'type', ClauseSeverity.OPTIONAL)
        
        graph.add_node(mandatory)
        graph.add_node(advisory)
        graph.add_node(optional)
        
        assert graph.nodes[0].severity == ClauseSeverity.MANDATORY
        assert graph.nodes[1].severity == ClauseSeverity.ADVISORY
        assert graph.nodes[2].severity == ClauseSeverity.OPTIONAL


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3: OwnershipState Tests (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOwnershipState:
    """Test OwnershipState tracking."""
    
    def test_create_ownership_state(self):
        """Test 46: Create ownership state."""
        state = OwnershipState(
            address=0x1000,
            kind=OwnershipKind.CALLER_OWNED,
            allocated_at='2024-01-01T00:00:00Z',
            allocated_by='caller'
        )
        assert state.address == 0x1000
        assert state.kind == OwnershipKind.CALLER_OWNED
        assert state.allocated_by == 'caller'
    
    def test_transfer_ownership(self):
        """Test 47: Transfer ownership."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED, 
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.transfer_to('callee', '2024-01-01T00:01:00Z')
        
        assert state.allocated_by == 'callee'
        assert len(state.transfer_history) == 1
    
    def test_transfer_history_recorded(self):
        """Test 48: Transfer history contains details."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.transfer_to('callee', '2024-01-01T00:01:00Z')
        
        history = state.transfer_history[0]
        assert history['from'] == 'caller'
        assert history['to'] == 'callee'
        assert 'timestamp' in history
        # NOTE: The actual validation logic might format the time string slightly differently
        # (e.g. adding 'Z') so checking for exact iso format needs care if using strict checks.
        assert history['previous_kind'] == 'caller_owned'
    
    def test_mark_freed(self):
        """Test 49: Mark pointer as freed."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.mark_freed('2024-01-01T00:02:00Z')
        
        assert state.kind == OwnershipKind.FREED
        assert not state.free_eligible
    
    def test_mark_freed_records_event(self):
        """Test 50: Freed event recorded in history."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.mark_freed('2024-01-01T00:02:00Z')
        
        assert len(state.transfer_history) == 1
        assert state.transfer_history[0]['event'] == 'freed'
    
    def test_double_free_raises(self):
        """Test 51: Double-free raises error."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.mark_freed('2024-01-01T00:02:00Z')
        
        with pytest.raises(ValueError, match='Double-free'):
            state.mark_freed('2024-01-01T00:03:00Z')
    
    def test_transfer_freed_pointer_raises(self):
        """Test 52: Cannot transfer freed pointer."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.mark_freed('2024-01-01T00:02:00Z')
        
        with pytest.raises(ValueError, match='freed'):
            state.transfer_to('someone', '2024-01-01T00:03:00Z')
    
    def test_ownership_state_to_dict(self):
        """Test 53: Ownership state serialization."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        data = state.to_dict()
        
        assert data['address'] == '0x1000'
        assert data['kind'] == 'caller_owned'
        assert data['allocated_by'] == 'caller'
        assert data['free_eligible'] is True
    
    def test_metadata_storage(self):
        """Test 54: Metadata storage."""
        metadata = {'source': 'malloc', 'size': 1024}
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller',
            metadata=metadata
        )
        assert state.metadata['source'] == 'malloc'
        assert state.metadata['size'] == 1024
    
    def test_free_eligible_default(self):
        """Test 55: Free eligible by default."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        assert state.free_eligible is True
    
    def test_transfer_preserves_address(self):
        """Test 56: Transfer preserves address."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.transfer_to('callee', '2024-01-01T00:01:00Z')
        assert state.address == 0x1000
    
    def test_multiple_transfers(self):
        """Test 57: Multiple ownership transfers."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.transfer_to('callee1', '2024-01-01T00:01:00Z')
        state.transfer_to('callee2', '2024-01-01T00:02:00Z')
        state.transfer_to('callee3', '2024-01-01T00:03:00Z')
        
        assert len(state.transfer_history) == 3
        assert state.allocated_by == 'callee3'
    
    def test_ownership_kinds(self):
        """Test 58: Different ownership kinds."""
        kinds = [
            OwnershipKind.CALLER_OWNED,
            OwnershipKind.CALLEE_OWNED,
            OwnershipKind.SHARED,
            OwnershipKind.TRANSFERRED,
        ]
        
        for kind in kinds:
            state = OwnershipState(
                0x1000, kind, '2024-01-01T00:00:00Z', 'owner'
            )
            assert state.kind == kind
    
    def test_to_dict_with_history(self):
        """Test 59: to_dict includes transfer history."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        state.transfer_to('callee', '2024-01-01T00:01:00Z')
        
        data = state.to_dict()
        assert 'transfer_history' in data
        assert len(data['transfer_history']) == 1
    
    def test_freed_not_free_eligible(self):
        """Test 60: Freed pointer not free eligible."""
        state = OwnershipState(
            0x1000, OwnershipKind.CALLER_OWNED,
            '2024-01-01T00:00:00Z', 'caller'
        )
        
        assert state.free_eligible is True
        state.mark_freed('2024-01-01T00:02:00Z')
        assert state.free_eligible is False

# ════════════════════════════════════════════════════════════════════════════
# SECTION 4: EnforcementContext Tests (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestEnforcementContext:
    """EnforcementContext tests (15 tests)."""
    
    def test_create_context(self):
        """Test 61: Create context."""
        ctx = EnforcementContext('func', 'uuid')
        assert ctx.function_name == 'func'
    
    def test_record_validation(self):
        """Test 62: Record validation."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_validation('c1', ValidationStatus.PASS)
        assert len(ctx.validation_results) == 1
    
    def test_record_crash(self):
        """Test 63: Record crash."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_crash(ValueError('test'), {})
        assert ctx.crashed is True
    
    def test_to_dict(self):
        """Test 64: Context to dict."""
        ctx = EnforcementContext('func', 'uuid')
        data = ctx.to_dict()
        assert 'function_name' in data
    
    def test_multiple_validations(self):
        """Test 65: Multiple validation records."""
        ctx = EnforcementContext('func', 'uuid')
        for i in range(10):
            ctx.record_validation(f'c{i}', ValidationStatus.PASS)
        assert len(ctx.validation_results) == 10
        
    def test_ctx_crash_info(self):
        """Test 66: Crash info details."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_crash(ValueError('test'), {'key': 'val'})
        assert ctx.crash_info['exception_type'] == 'ValueError'
        
    def test_ctx_start_time(self):
        """Test 67: Start time recorded."""
        ctx = EnforcementContext('func', 'uuid', start_time='now')
        assert ctx.start_time == 'now'
        
    def test_ctx_ownership_deltas(self):
        """Test 68: Ownership deltas initialized."""
        ctx = EnforcementContext('func', 'uuid')
        assert ctx.ownership_deltas == []
        
    def test_ctx_invocation_id(self):
        """Test 69: Invocation ID stored."""
        ctx = EnforcementContext('func', 'my-id')
        assert ctx.invocation_id == 'my-id'
        
    def test_validation_result_structure(self):
        """Test 70: Validation result has required fields."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_validation('c1', ValidationStatus.PASS, 'ok')
        res = ctx.validation_results[0]
        assert 'clause_id' in res
        assert 'status' in res
        assert 'message' in res
        assert 'timestamp' in res

    def test_validation_status_value(self):
        """Test 71: Validation status stored as value."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_validation('c1', ValidationStatus.FAIL)
        assert ctx.validation_results[0]['status'] == 'fail'

    def test_record_crash_timestamp(self):
        """Test 72: Crash record includes timestamp."""
        ctx = EnforcementContext('func', 'uuid')
        ctx.record_crash(Exception(), {})
        assert 'timestamp' in ctx.crash_info

    def test_context_equality_logic(self):
        """Test 73: Context basic equality."""
        # Not logically equal if different IDs
        ctx1 = EnforcementContext('func', 'uuid1')
        ctx2 = EnforcementContext('func', 'uuid2')
        assert ctx1 != ctx2

    def test_normalized_inputs_storage(self):
        """Test 74: Normalized inputs storage."""
        inputs = [1, "test"]
        ctx = EnforcementContext('func', 'uuid', normalized_inputs=inputs)
        assert ctx.normalized_inputs == inputs

    def test_end_time_storage(self):
        """Test 75: End time storage."""
        ctx = EnforcementContext('func', 'uuid', end_time='later')
        assert ctx.end_time == 'later'


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5: ViolationReport Tests (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestViolationReport:
    """ViolationReport tests (15 tests)."""
    
    def test_create_report(self):
        """Test 76: Create report."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        assert r.function_name == 'f'
    
    def test_to_dict(self):
        """Test 77: Report to dict."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        data = r.to_dict()
        assert 'clause_id' in data
    
    def test_to_json(self):
        """Test 78: Report to JSON."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        j = r.to_json()
        assert isinstance(j, str)
        assert '"function_name": "f"' in j
    
    def test_severity_preserved(self):
        """Test 79: Severity preserved."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.ADVISORY,
                           'e', 'o', 'm', 'fp', 'ts')
        assert r.severity == ClauseSeverity.ADVISORY

    def test_report_message(self):
        """Test 80: Report message stored."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'Test Violation', 'fp', 'ts')
        assert r.message == 'Test Violation'

    def test_report_expected(self):
        """Test 81: Expected value stored."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'Exp', 'o', 'm', 'fp', 'ts')
        assert r.expected == 'Exp'

    def test_report_observed(self):
        """Test 82: Observed value stored."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'Obs', 'm', 'fp', 'ts')
        assert r.observed == 'Obs'

    def test_report_fingerprint(self):
        """Test 83: Fingerprint stored."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'Fingerprint123', 'ts')
        assert r.contract_fingerprint == 'Fingerprint123'

    def test_report_timestamp(self):
        """Test 84: Timestamp stored."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', '2024-01-01')
        assert r.timestamp == '2024-01-01'

    def test_remediation_hints(self):
        """Test 85: Remediation hints."""
        hints = ["Fix param", "Check bounds"]
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts', remediation_hints=hints)
        assert len(r.remediation_hints) == 2

    def test_invocation_context(self):
        """Test 86: Invocation context."""
        ctx = {"param": 1}
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts', invocation_context=ctx)
        assert r.invocation_context['param'] == 1

    def test_to_dict_severity_value(self):
        """Test 87: to_dict uses severity string value."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        assert r.to_dict()['severity'] == 'mandatory'

    def test_default_empty_hints(self):
        """Test 88: Default hints empty."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        assert r.remediation_hints == []

    def test_default_empty_context(self):
        """Test 89: Default context empty."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        assert r.invocation_context == {}

    def test_json_indent(self):
        """Test 90: JSON indent works."""
        r = ViolationReport('f', 'c', 't', ClauseSeverity.MANDATORY,
                           'e', 'o', 'm', 'fp', 'ts')
        j = r.to_json(indent=4)
        assert '\n    "function_name":' in j  # Check 4-space indent


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6: ContractProjector Tests (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestContractProjector:
    """ContractProjector tests (15 tests)."""
    
    @pytest.fixture
    def sample_contract(self):
        return {
            'schema_version': '1.0.0',
            'contract_id': 'test',
            'functions': {
                'test_func': {
                    'parameters': [{
                        'name': 'p0',
                        'clauses': [{
                            'clause_id': 'c1',
                            'clause_type': 'range',
                            'severity': 'mandatory'
                        }]
                    }]
                }
            }
        }
    
    def test_create_projector(self):
        """Test 91: Create projector."""
        p = ContractProjector()
        assert p.contract_cache == {}
    
    def test_compute_fingerprint(self, sample_contract):
        """Test 92: Compute fingerprint."""
        p = ContractProjector()
        fp = p._compute_fingerprint(sample_contract)
        assert len(fp) == 64
        # Deterministic
        assert fp == p._compute_fingerprint(sample_contract) 
    
    def test_validate_structure(self, sample_contract):
        """Test 93: Validate structure."""
        p = ContractProjector()
        p._validate_contract_structure(sample_contract)
    
    def test_missing_field_raises(self):
        """Test 94: Missing field raises."""
        p = ContractProjector()
        with pytest.raises(ValueError, match="missing required field"):
            p._validate_contract_structure({})
    
    def test_bad_schema_version(self):
        """Test 95: Bad schema version raises."""
        p = ContractProjector()
        with pytest.raises(ValueError, match="Unsupported schema version"):
            p._validate_contract_structure({
                'schema_version': '2.0.0', 
                'contract_id': 't', 
                'functions': {}
            })

    def test_project_function(self, sample_contract):
        """Test 96: Project function."""
        p = ContractProjector()
        graph = p.project_function(sample_contract, 'test_func')
        assert graph.function_name == 'test_func'
        assert len(graph.nodes) == 1
        assert graph.nodes[0].clause_id == 'c1'

    def test_project_missing_function(self, sample_contract):
        """Test 97: Project missing function raises."""
        p = ContractProjector()
        with pytest.raises(ValueError, match="Function not found"):
            p.project_function(sample_contract, 'missing')

    def test_create_node_defaults(self):
        """Test 98: Node creation uses defaults."""
        p = ContractProjector()
        clause = {'clause_id': 'c1'} # Minimal
        node = p._create_node(clause, 0, 'p0')
        assert node.clause_type == 'unknown'
        assert node.severity == ClauseSeverity.MANDATORY

    def test_create_node_custom(self):
        """Test 99: Node creation uses provided values."""
        p = ContractProjector()
        clause = {
            'clause_id': 'c1', 
            'clause_type': 'custom', 
            'severity': 'advisory',
            'failure_message': 'fail'
        }
        node = p._create_node(clause, 0, 'p0')
        assert node.clause_type == 'custom'
        assert node.severity == ClauseSeverity.ADVISORY
        assert node.failure_message == 'fail'

    def test_load_contract_file(self, sample_contract):
        """Test 100: Load contract from file."""
        p = ContractProjector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_contract, f)
            path = f.name
        
        try:
            loaded = p.load_contract(path)
            assert loaded['contract_id'] == 'test'
            assert len(p.contract_cache) == 1
        finally:
            os.unlink(path)

    def test_load_contract_not_found(self):
        """Test 101: Load missing file raises."""
        p = ContractProjector()
        with pytest.raises(FileNotFoundError):
            p.load_contract("non_existent_file.json")

    def test_project_multiple_clauses(self):
        """Test 102: Project multiple clauses."""
        contract = {
            'schema_version': '1.0.0', 'contract_id': 't',
            'functions': {
                'f': {
                    'parameters': [{
                        'name': 'p',
                        'clauses': [
                            {'clause_id': 'c1'}, {'clause_id': 'c2'}
                        ]
                    }]
                }
            }
        }
        p = ContractProjector()
        graph = p.project_function(contract, 'f')
        assert len(graph.nodes) == 2

    def test_bad_severity_fallback(self):
        """Test 103: Bad severity falls back to mandatory."""
        p = ContractProjector()
        clause = {'clause_id': 'c1', 'severity': 'INVALID'}
        node = p._create_node(clause, 0, 'p')
        assert node.severity == ClauseSeverity.MANDATORY

    def test_project_param_indices(self):
        """Test 104: Parameter indices assigned correctly."""
        p = ContractProjector()
        clause = {'clause_id': 'c1'}
        node = p._create_node(clause, 5, 'p5')
        assert node.parameters == [5]

    def test_caching_behavior(self, sample_contract):
        """Test 105: Contracts are cached."""
        p = ContractProjector()
        # Mocking or file IO needed to fully test, but we can check internal state logic
        # Here we manually populate and check
        fp = p._compute_fingerprint(sample_contract)
        p.contract_cache[fp] = sample_contract
        assert fp in p.contract_cache

# ════════════════════════════════════════════════════════════════════════════
# SECTION 7: OwnershipRegistry Tests (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestOwnershipRegistry:
    """OwnershipRegistry tests (10 tests)."""
    
    def test_create_registry(self):
        """Test 106: Create registry."""
        r = OwnershipRegistry()
        assert r.allocation_counter == 0
    
    def test_register_allocation(self):
        """Test 107: Register allocation."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        assert r.allocation_counter == 1
    
    def test_get_state(self):
        """Test 108: Get state."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        state = r.get_state(0x1000)
        assert state is not None
        assert state.address == 0x1000
    
    def test_transfer_ownership(self):
        """Test 109: Transfer ownership."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        r.transfer_ownership(0x1000, 'callee', OwnershipKind.CALLEE_OWNED)
        assert r.get_state(0x1000).allocated_by == 'callee'
        assert r.get_state(0x1000).kind == OwnershipKind.CALLEE_OWNED
    
    def test_mark_freed(self):
        """Test 110: Mark freed."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        r.mark_freed(0x1000)
        assert r.get_state(0x1000).kind == OwnershipKind.FREED
    
    def test_double_free_raises(self):
        """Test 111: Double free detection."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        r.mark_freed(0x1000)
        with pytest.raises(ValueError, match='Double-free'):
            r.mark_freed(0x1000)

    def test_transfer_unregistered_raises(self):
        """Test 112: Transfer unknown raises."""
        r = OwnershipRegistry()
        with pytest.raises(ValueError, match="not registered"):
            r.transfer_ownership(0x999, 'callee', OwnershipKind.SHARED)

    def test_free_unregistered_raises(self):
        """Test 113: Free unknown raises."""
        r = OwnershipRegistry()
        with pytest.raises(ValueError, match="not registered"):
            r.mark_freed(0x999)

    def test_clear_registry(self):
        """Test 114: Clear registry."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        r.clear()
        assert r.allocation_counter == 0
        assert len(r.registry) == 0

    def test_get_statistics(self):
        """Test 115: Registry stats."""
        r = OwnershipRegistry()
        r.register_allocation(0x1000, OwnershipKind.CALLER_OWNED, 'caller')
        r.register_allocation(0x2000, OwnershipKind.CALLER_OWNED, 'caller')
        r.mark_freed(0x2000)
        stats = r.get_statistics()
        assert stats['total_allocations'] == 2
        assert stats['active_pointers'] == 1
        assert stats['freed_pointers'] == 1


# ════════════════════════════════════════════════════════════════════════════
# SECTION 8: LanguageAdapter Tests (5 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestLanguageAdapter:
    """LanguageAdapter tests (5 tests)."""
    
    def test_create_adapter(self):
        """Test 116: Create adapter."""
        a = LanguageAdapter()
        assert a.config is not None
        assert a.projector is not None
        assert a.ownership_registry is not None
    
    def test_adapter_with_config(self):
        """Test 117: Adapter with custom config."""
        cfg = AdapterConfig(mode=EnforcementMode.STRICT)
        a = LanguageAdapter(cfg)
        assert a.config.mode == EnforcementMode.STRICT
    
    def test_create_context(self):
        """Test 118: Create enforcement context."""
        a = LanguageAdapter()
        ctx = a.create_enforcement_context('func')
        assert ctx.function_name == 'func'
        assert ctx.invocation_id is not None
    
    def test_get_statistics(self):
        """Test 119: Get statistics."""
        a = LanguageAdapter()
        stats = a.get_statistics()
        assert 'config' in stats
        assert 'contract_fingerprint' in stats
        assert 'ownership' in stats
    
    def test_empty_graphs(self):
        """Test 120: Empty validation graphs."""
        a = LanguageAdapter()
        assert len(a.validation_graphs) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
