"""
Test Case Executor
Handles the execution of a single FFI test case in isolation.
"""

import time
import traceback
from typing import Any, Dict, Optional
from .input_instantiator import InputInstantiator
from .outcome_validator import OutcomeValidator

class TestCaseExecutor:
    """
    Executes a single test case and records the outcome.
    """

    def __init__(self, instantiator: InputInstantiator, validator: OutcomeValidator):
        self.instantiator = instantiator
        self.validator = validator

    def execute(self, test_case: Dict[str, Any], adapter_module: Any) -> Dict[str, Any]:
        """
        Executes the test case.
        """
        test_id = test_case["test_id"]
        func_name = test_case["function_name"]
        expected = test_case["expected_outcome"]
        
        result = {
            "test_id": test_id,
            "test_category": test_case["test_category"],
            "function_name": func_name,
            "execution_start_time": time.time(),
            "status": "failed",
            "constraints_exercised": test_case.get("constraints_exercised", [])
        }

        try:
            # 1. Instantiate Inputs
            # In , inputs are mapped by parameter name
            kwargs = {}
            for p_name, p_spec in test_case["inputs"].items():
                kwargs[p_name] = self.instantiator.instantiate(p_spec)
            
            # 2. Get Adapter Function
            # The adapter module contains functions with the same name as native functions
            func = getattr(adapter_module, func_name, None)
            if not func:
                result["actual_outcome"] = {"type": "error", "message": f"Function {func_name} not found in adapter"}
                result["failure_reason"] = f"Adapter missing function: {func_name}"
                return result

            # 3. Invoke
            start_perf = time.perf_counter()
            actual_ret = None
            actual_outcome = {"type": "success"}
            
            try:
                actual_ret = func(**kwargs)
                actual_outcome["return_value"] = str(actual_ret) # Stringify for JSON
            except Exception as e:
                # Classify exception
                # Our exceptions usually have a 'constraint_id' attribute
                actual_outcome = {
                    "type": "exception",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "constraint_id": getattr(e, "constraint_id", None)
                }
            
            duration_ms = (time.perf_counter() - start_perf) * 1000
            
            # 4. Validate
            success, reason = self.validator.validate(expected, actual_outcome)
            
            result["status"] = "passed" if success else "failed"
            result["actual_outcome"] = actual_outcome
            result["duration_ms"] = duration_ms
            if not success:
                result["failure_reason"] = reason

        except Exception as e:
            result["status"] = "failed"
            result["actual_outcome"] = {"type": "error", "message": str(e)}
            result["failure_reason"] = f"Internal executor error: {str(e)}"
            result["traceback"] = traceback.format_exc()

        result["execution_end_time"] = time.time()
        return result
