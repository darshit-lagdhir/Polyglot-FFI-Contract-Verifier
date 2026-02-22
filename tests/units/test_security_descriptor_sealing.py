import pytest
from dataclasses import asdict
from modules.module_08_language_adapter.language_adapter import (
    ValidationNode, ValidationGraph, ClauseSeverity, SecurityViolationError
)

def test_node_sealing():
    node = ValidationNode(
        clause_id="C1",
        clause_type="range",
        severity=ClauseSeverity.FATAL
    )
    node.seal()
    
    with pytest.raises(SecurityViolationError) as excinfo:
        node.clause_id = "C2"
    assert "Attempted mutation of sealed descriptor" in str(excinfo.value)

def test_graph_sealing():
    graph = ValidationGraph(function_name="test_func")
    graph.seal()
    
    with pytest.raises(SecurityViolationError) as excinfo:
        graph.function_name = "mutated"
    assert "Attempted mutation of sealed descriptor" in str(excinfo.value)
