"""
Subprocess Test Executor
Entry point for child processes executing individual FFI test cases.
"""

import sys
import os
import json
import traceback
import importlib
from typing import Any, Dict

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.verification.input_instantiator import InputInstantiator

def run_test(test_case_json: str, lib_name: str, adapter_module_name: str):
    """
    Executes a single test case and prints the result as JSON to stdout.
    """
    try:
        test_case = json.loads(test_case_json)
        
        # Add adapters to path
        adapters_dir = os.path.abspath("adapters")
        if adapters_dir not in sys.path:
            sys.path.append(adapters_dir)
            
        # Load adapter
        adapter_module = importlib.import_module(adapter_module_name)
        
        # Initialize instantiator
        instantiator = InputInstantiator(lib_name)
        
        # Instantiate inputs
        kwargs = {}
        for p_name, p_spec in test_case["inputs"].items():
            kwargs[p_name] = instantiator.instantiate(p_spec)
            
        # Get function
        func_name = test_case["function_name"]
        func = getattr(adapter_module, func_name)
        
        # Execute
        actual_outcome = {"type": "success"}
        try:
            actual_ret = func(**kwargs)
            actual_outcome["return_value"] = str(actual_ret)
        except Exception as e:
            actual_outcome = {
                "type": "exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "constraint_id": getattr(e, "constraint_id", None)
            }
            
        # Print result
        print("---RESULT_START---")
        print(json.dumps(actual_outcome))
        print("---RESULT_END---")
        
    except Exception as e:
        error_info = {
            "type": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print("---RESULT_START---")
        print(json.dumps(error_info))
        print("---RESULT_END---")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(2)
    
    run_test(sys.argv[1], sys.argv[2], sys.argv[3])
