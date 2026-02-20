# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 6459902ff80c5d51
# ==============================================================================

"""Testing utilities and mock FFI framework for Language Adapter."""

from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


# ════════════════════════════════════════════════════════════════════════════
# SECTION 86: INVOCATION TRACKER
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Invocation:
    """Records a single function invocation."""
    function_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    timestamp: str
    result: Any = None
    raised_exception: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'function_name': self.function_name,
            'args': list(self.args),
            'kwargs': self.kwargs,
            'timestamp': self.timestamp,
            'result': str(self.result),
            'raised_exception': str(self.raised_exception) if self.raised_exception else None
        }


class InvocationTracker:
    """
    Tracks function invocations for testing.
    
    Records all calls and provides query interface for verification.
    """

    def __init__(self):
        self.invocations: List[Invocation] = []

    def record(
        self,
        function_name: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        result: Any = None,
        exception: Optional[Exception] = None
    ) -> None:
        """
        Record invocation.
        
        Args:
            function_name: Function name
            args: Positional arguments
            kwargs: Keyword arguments
            result: Return value
            exception: Raised exception
        """
        invocation = Invocation(
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            result=result,
            raised_exception=exception
        )
        self.invocations.append(invocation)

    def get_invocations(
        self,
        function_name: Optional[str] = None
    ) -> List[Invocation]:
        """
        Get invocations, optionally filtered by function name.
        
        Args:
            function_name: Optional function name filter
            
        Returns:
            List of invocations
        """
        if function_name is None:
            return self.invocations
        
        return [inv for inv in self.invocations if inv.function_name == function_name]

    def get_call_count(self, function_name: str) -> int:
        """Get number of times function was called."""
        return len(self.get_invocations(function_name))

    def was_called_with(
        self,
        function_name: str,
        *args,
        **kwargs
    ) -> bool:
        """
        Check if function was called with specific arguments.
        
        Args:
            function_name: Function name
            *args: Expected arguments
            **kwargs: Expected keyword arguments
            
        Returns:
            True if matching invocation found
        """
        invocations = self.get_invocations(function_name)
        
        for inv in invocations:
            if inv.args == args and inv.kwargs == kwargs:
                return True
        
        return False

    def clear(self) -> None:
        """Clear all recorded invocations."""
        self.invocations.clear()


# ════════════════════════════════════════════════════════════════════════════
# SECTION 87: BEHAVIOR SIMULATOR
# ════════════════════════════════════════════════════════════════════════════

class BehaviorSimulator:
    """
    Simulates various FFI function behaviors.
    
    Provides configurable behaviors for mock functions.
    """

    @staticmethod
    def return_value(value: Any) -> Callable:
        """
        Create behavior that returns fixed value.
        
        Args:
            value: Value to return
            
        Returns:
            Behavior function
        """
        def behavior(*args, **kwargs):
            return value
        return behavior

    @staticmethod
    def raise_exception(exception: Exception) -> Callable:
        """
        Create behavior that raises exception.
        
        Args:
            exception: Exception to raise
            
        Returns:
            Behavior function
        """
        def behavior(*args, **kwargs):
            raise exception
        return behavior

    @staticmethod
    def compute_from_args(computation: Callable) -> Callable:
        """
        Create behavior that computes result from arguments.
        
        Args:
            computation: Function to compute result
            
        Returns:
            Behavior function
        """
        return computation

    @staticmethod
    def modify_buffer(buffer_index: int, new_data: bytes) -> Callable:
        """
        Create behavior that modifies buffer argument.
        
        Args:
            buffer_index: Index of buffer argument
            new_data: Data to write to buffer
            
        Returns:
            Behavior function
        """
        def behavior(*args, **kwargs):
            if buffer_index < len(args):
                buffer = args[buffer_index]
                if isinstance(buffer, bytearray):
                    buffer[:len(new_data)] = new_data
            return 0  # Success
        return behavior

    @staticmethod
    def conditional_behavior(
        condition: Callable,
        true_behavior: Callable,
        false_behavior: Callable
    ) -> Callable:
        """
        Create behavior that depends on condition.
        
        Args:
            condition: Condition function
            true_behavior: Behavior if condition true
            false_behavior: Behavior if condition false
            
        Returns:
            Behavior function
        """
        def behavior(*args, **kwargs):
            if condition(*args, **kwargs):
                return true_behavior(*args, **kwargs)
            else:
                return false_behavior(*args, **kwargs)
        return behavior


# ════════════════════════════════════════════════════════════════════════════
# SECTION 88: MOCK FFI FUNCTION
# ════════════════════════════════════════════════════════════════════════════

class MockFFIFunction:
    """
    Mock FFI function for testing.
    
    Simulates native function behavior without requiring native code.
    """

    def __init__(
        self,
        name: str,
        behavior: Optional[Callable] = None,
        tracker: Optional[InvocationTracker] = None
    ):
        """
        Initialize mock FFI function.
        
        Args:
            name: Function name
            behavior: Behavior function
            tracker: Invocation tracker
        """
        self.name = name
        self.behavior = behavior or BehaviorSimulator.return_value(0)
        self.tracker = tracker or InvocationTracker()

    def __call__(self, *args, **kwargs) -> Any:
        """
        Invoke mock function.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from behavior function
        """
        result = None
        exception = None
        
        try:
            result = self.behavior(*args, **kwargs)
            self.tracker.record(self.name, args, kwargs, result=result)
            return result
        except Exception as e:
            exception = e
            self.tracker.record(self.name, args, kwargs, exception=exception)
            raise

    def set_behavior(self, behavior: Callable) -> None:
        """Set new behavior."""
        self.behavior = behavior

    def get_call_count(self) -> int:
        """Get number of times function was called."""
        return self.tracker.get_call_count(self.name)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 89: CONTRACT TEST BUILDER
# ════════════════════════════════════════════════════════════════════════════

class ContractTestBuilder:
    """
    Builds contract tests declaratively.
    
    Provides fluent interface for defining contract test cases.
    """

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.test_cases: List[Dict[str, Any]] = []

    def with_valid_inputs(
        self,
        inputs: List[Any],
        expected_result: Any
    ) -> 'ContractTestBuilder':
        """
        Add test case with valid inputs.
        
        Args:
            inputs: Input values
            expected_result: Expected result
            
        Returns:
            Self for chaining
        """
        self.test_cases.append({
            'type': 'valid',
            'inputs': inputs,
            'expected_result': expected_result
        })
        return self

    def with_invalid_inputs(
        self,
        inputs: List[Any],
        expected_clause: str
    ) -> 'ContractTestBuilder':
        """
        Add test case with invalid inputs.
        
        Args:
            inputs: Input values
            expected_clause: Expected violating clause
            
        Returns:
            Self for chaining
        """
        self.test_cases.append({
            'type': 'invalid',
            'inputs': inputs,
            'expected_clause': expected_clause
        })
        return self

    def build_contract(self) -> Dict[str, Any]:
        """
        Build contract from test cases.
        
        Returns:
            Contract dictionary
        """
        # Infer contract structure from test cases
        contract = {
            'contract_id': f'test_{self.function_name}',
            'schema_version': '1.0.0',
            'functions': {
                self.function_name: {
                    'parameters': [],
                    'return': {'type': 'int'}
                }
            }
        }
        
        return contract

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases."""
        return self.test_cases


# ════════════════════════════════════════════════════════════════════════════
# SECTION 90: ASSERTION HELPERS
# ════════════════════════════════════════════════════════════════════════════

class AssertionHelpers:
    """
    Custom assertions for FFI testing.
    
    Provides domain-specific assertions for common test patterns.
    """

    @staticmethod
    def assert_validation_passed(result: Dict[str, Any]) -> None:
        """
        Assert that validation passed.
        
        Args:
            result: Invocation result
            
        Raises:
            AssertionError: If validation failed
        """
        if not result.get('success'):
            raise AssertionError(
                f"Validation failed: {result.get('failed_phase')}"
            )

    @staticmethod
    def assert_validation_failed(
        result: Dict[str, Any],
        expected_clause: Optional[str] = None
    ) -> None:
        """
        Assert that validation failed.
        
        Args:
            result: Invocation result
            expected_clause: Expected failing clause
            
        Raises:
            AssertionError: If validation passed or wrong clause failed
        """
        if result.get('success'):
            raise AssertionError("Expected validation to fail, but it passed")
        
        if expected_clause:
            phases = result.get('phases', [])
            for phase in phases:
                if phase.get('violations'):
                    for violation in phase['violations']:
                        if violation.get('clause_id') == expected_clause:
                            return
            
            raise AssertionError(
                f"Expected clause '{expected_clause}' to fail, but it didn't"
            )

    @staticmethod
    def assert_ownership_state(
        graph: Any,
        address: int,
        expected_owner: str
    ) -> None:
        """
        Assert ownership state.
        
        Args:
            graph: Ownership graph
            address: Memory address
            expected_owner: Expected owner
            
        Raises:
            AssertionError: If owner doesn't match
        """
        actual_owner = graph.get_owner(address)
        if actual_owner != expected_owner:
            raise AssertionError(
                f"Expected owner '{expected_owner}', got '{actual_owner}'"
            )

    @staticmethod
    def assert_called_with(
        tracker: InvocationTracker,
        function_name: str,
        *args,
        **kwargs
    ) -> None:
        """
        Assert function was called with specific arguments.
        
        Args:
            tracker: Invocation tracker
            function_name: Function name
            *args: Expected arguments
            **kwargs: Expected keyword arguments
            
        Raises:
            AssertionError: If not called with arguments
        """
        if not tracker.was_called_with(function_name, *args, **kwargs):
            raise AssertionError(
                f"Function '{function_name}' was not called with expected arguments"
            )


# ════════════════════════════════════════════════════════════════════════════
# SECTION 91: TEST FIXTURES
# ════════════════════════════════════════════════════════════════════════════

class TestFixtures:
    """
    Reusable test fixtures.
    
    Provides common test data and configurations.
    """

    @staticmethod
    def sample_contract() -> Dict[str, Any]:
        """Get sample contract for testing."""
        return {
            'contract_id': 'test_contract',
            'schema_version': '1.0.0',
            'functions': {
                'add': {
                    'name': 'add',
                    'parameters': [
                        {
                            'name': 'a',
                            'type': 'int',
                            'clauses': [
                                {
                                    'clause_id': 'a_range',
                                    'clause_type': 'range',
                                    'severity': 'mandatory',
                                    'metadata': {'min': 0, 'max': 100}
                                }
                            ]
                        },
                        {
                            'name': 'b',
                            'type': 'int',
                            'clauses': []
                        }
                    ],
                    'return': {'type': 'int'}
                }
            }
        }

    @staticmethod
    def create_mock_function(
        name: str = 'test_func',
        return_value: Any = 0
    ) -> MockFFIFunction:
        """
        Create mock FFI function.
        
        Args:
            name: Function name
            return_value: Value to return
            
        Returns:
            Mock function
        """
        behavior = BehaviorSimulator.return_value(return_value)
        return MockFFIFunction(name, behavior)

    @staticmethod
    def sample_buffers() -> Dict[str, Any]:
        """Get sample buffers for testing."""
        return {
            'small': bytearray(64),
            'medium': bytearray(1024),
            'large': bytearray(4096),
            'bytes': b'test data',
            'empty': bytearray(0)
        }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 92: TEST RUNNER
# ════════════════════════════════════════════════════════════════════════════

class FFITestRunner:
    """
    Test runner for FFI contract tests.
    
    Executes contract test cases and reports results.
    """

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def run_test_case(
        self,
        adapter: Any,
        function_name: str,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run single test case.
        
        Args:
            adapter: Adapter instance
            function_name: Function name
            test_case: Test case definition
            
        Returns:
            Test result
        """
        result = {
            'function': function_name,
            'type': test_case['type'],
            'passed': False,
            'message': ''
        }
        
        try:
            if test_case['type'] == 'valid':
                # Test with valid inputs
                inputs = test_case['inputs']
                mock_func = lambda *args: test_case['expected_result']
                
                actual_result = adapter.call_with_enforcement(
                    function_name,
                    *inputs,
                    native_callable=mock_func
                )
                
                if actual_result == test_case['expected_result']:
                    result['passed'] = True
                else:
                    result['message'] = f"Expected {test_case['expected_result']}, got {actual_result}"
            
            elif test_case['type'] == 'invalid':
                # Test with invalid inputs - should raise exception
                from modules.module_08_language_adapter import ContractViolationError
                
                try:
                    inputs = test_case['inputs']
                    adapter.call_with_enforcement(
                        function_name,
                        *inputs,
                        native_callable=lambda *args: 0
                    )
                    result['message'] = "Expected ContractViolationError but none was raised"
                except ContractViolationError:
                    result['passed'] = True
        
        except Exception as e:
            result['message'] = f"Unexpected exception: {e}"
        
        self.results.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total = len(self.results)
        passed = len([r for r in self.results if r['passed']])
        
        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0.0
        }


# Export all testing utilities
__all__ = [
    'Invocation',
    'InvocationTracker',
    'BehaviorSimulator',
    'MockFFIFunction',
    'ContractTestBuilder',
    'AssertionHelpers',
    'TestFixtures',
    'FFITestRunner',
]