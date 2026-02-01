"""
Verification Executor
The primary entry point for Phase 8.
"""

import os
import json
import sys
from typing import Any, Dict, List

from .test_case_executor import TestCaseExecutor
from .input_instantiator import InputInstantiator
from .outcome_validator import OutcomeValidator
from .execution_logger import ExecutionLogger
from .execution_summary_generator import ExecutionSummaryGenerator

class VerificationExecutor:
    """
    Orchestrates the verification process.
    """

    def execute(self, context) -> Dict[str, Any]:
        """
        Executes the full verification cycle.
        """
        # 1. Load Artefacts
        plan_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "test_plan.json")
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Test plan missing: {plan_path}. Run 'generate-tests' first.")
            
        with open(plan_path, 'r') as f:
            test_plan = json.load(f)
            
        # 2. Setup Environment
        lib_name = os.path.splitext(os.path.basename(context.native_library.library_path))[0]
        
        # Add adapters to path
        adapters_dir = os.path.abspath("adapters")
        if adapters_dir not in sys.path:
            sys.path.append(adapters_dir)
            
        # 3. Load Adapter
        adapter_module_name = f"{lib_name}_adapter"
        try:
            # We use importlib to be clean
            import importlib
            adapter_module = importlib.import_module(adapter_module_name)
            # Reload to ensure we have the latest generated code
            importlib.reload(adapter_module)
        except ImportError as e:
            raise ImportError(f"Could not load adapter {adapter_module_name}: {e}. Run 'generate-adapters' first.")

        # 4. Initialize Components
        instantiator = InputInstantiator(lib_name)
        validator = OutcomeValidator()
        tc_executor = TestCaseExecutor(instantiator, validator)
        logger = ExecutionLogger()
        summary_gen = ExecutionSummaryGenerator()
        
        # 5. Execute Tests
        test_results = []
        for test_case in test_plan.get("test_cases", []):
            result = tc_executor.execute(test_case, adapter_module)
            test_results.append(result)
            
        # 6. Finalize Log
        log = logger.build_log(context, test_results, test_plan)
        
        # 7. Save Artifacts
        log_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "execution_log.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)
            
        summary = summary_gen.generate(log)
        summary_path = os.path.join(os.path.dirname(context.artifacts.contract_path), "execution_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        return log
