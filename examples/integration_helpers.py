"""Helper utilities for integration."""

import json
import tempfile
from typing import Any, Dict, List, Optional
from pathlib import Path

from modules.module_08_language_adapter import (
    PythonAdapterComplete,
    EnforcementContext,
)

class IntegrationHelpers:
    """Helper functions for adapter integration."""

    @staticmethod
    def create_simple_contract(
        function_name: str,
        param_types: List[str]
    ) -> Dict[str, Any]:
        """
        Create simple contract for quick testing.
        
        Args:
            function_name: Function name
            param_types: List of parameter types
            
        Returns:
            Contract dictionary
        """
        parameters = []
        for i, ptype in enumerate(param_types):
            parameters.append({
                'name': f'param{i}',
                'type': ptype,
                'clauses': []
            })
        
        return {
            'contract_id': f'simple_{function_name}',
            'schema_version': '1.0.0',
            'functions': {
                function_name: {
                    'name': function_name,
                    'parameters': parameters,
                    'return': {'type': 'int'}
                }
            }
        }

    @staticmethod
    def setup_test_adapter(
        contract: Dict[str, Any]
    ) -> PythonAdapterComplete:
        """
        Setup adapter for testing.
        
        Args:
            contract: Contract dictionary
            
        Returns:
            Configured adapter
        """
        # Save contract
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            contract_path = f.name
        
        # Create and configure adapter
        adapter = PythonAdapterComplete()
        adapter.load_contract(contract_path)
        
        # We can remove the file after loading as it's cached/projected
        try:
            import os
            os.unlink(contract_path)
        except OSError:
            pass
            
        return adapter

    @staticmethod
    def assert_no_violations(result: Dict[str, Any]) -> None:
        """
        Assert that invocation had no violations.
        
        Args:
            result: Invocation result dictionary (from invoke_with_enforcement)
            
        Raises:
            AssertionError: If violations found
        """
        if not result.get('success', True):
            phases = result.get('phases', [])
            for phase in phases:
                if phase.get('violations'):
                    violations = phase['violations']
                    raise AssertionError(
                        f"Contract violations found in phase '{phase['phase_name']}': {violations}"
                    )
            
            if result.get('failed_phase'):
                raise AssertionError(
                    f"Pipeline failed in phase '{result['failed_phase']}'"
                )
