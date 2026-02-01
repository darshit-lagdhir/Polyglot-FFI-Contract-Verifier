"""
Test Plan Generator
Orchestrates the creation of exhaustive test suites from FFI contracts.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from .input_value_generator import InputValueGenerator
from .positive_test_generator import PositiveTestGenerator
from .negative_test_generator import NegativeTestGenerator
from .boundary_value_test_generator import BoundaryValueTestGenerator
from .coverage_analyzer import CoverageAnalyzer

class TestPlanGenerator:
    """
    Main orchestrator for Phase 7.
    """
    
    def __init__(self):
        self.input_gen = InputValueGenerator()
        self.pos_gen = PositiveTestGenerator(self.input_gen)
        self.neg_gen = NegativeTestGenerator(self.input_gen)
        self.bound_gen = BoundaryValueTestGenerator(self.input_gen)
        self.coverage_analyzer = CoverageAnalyzer()

    def generate(self, context) -> Dict[str, Any]:
        """
        Generates a complete test plan based on the contract and IR.
        """
        contract_path = context.artifacts.contract_path
        ir_path = context.artifacts.intermediate_representation_path
        
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contract artifact not found: {contract_path}")
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}")
            
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        with open(ir_path, 'r') as f:
            ir = json.load(f)

        test_cases = []
        
        for f_contract in contract.get("function_contracts", []):
            # 1. Positive Tests
            test_cases.extend(self.pos_gen.generate_positive_tests(f_contract, ir))
            
            # 2. Negative Tests
            test_cases.extend(self.neg_gen.generate_negative_tests(f_contract, ir))
            
            # 3. Boundary Tests
            test_cases.extend(self.bound_gen.generate_boundary_tests(f_contract, ir))
            
        # Analyze Coverage
        coverage = self.coverage_analyzer.analyze_coverage(test_cases, contract)
        
        # Build Metadata
        metadata = {
            "total_test_cases": len(test_cases),
            "positive_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "positive"),
            "negative_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "negative"),
            "boundary_test_cases": sum(1 for tc in test_cases if tc["test_category"] == "boundary"),
            "constraint_coverage": coverage["summary"]
        }
        
        # Final Test Plan
        test_plan = {
            "provenance": {
                "producing_phase": "Phase 7: Test Plan Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(contract_path), os.path.abspath(ir_path)]
            },
            "test_suite_metadata": metadata,
            "test_cases": test_cases,
            "constraint_coverage_map": coverage["coverage_map"]
        }
        
        # Save artifacts
        plan_path = os.path.join(os.path.dirname(contract_path), "test_plan.json")
        with open(plan_path, 'w') as f:
            json.dump(test_plan, f, indent=2)
            
        coverage_path = os.path.join(os.path.dirname(contract_path), "test_coverage.json")
        with open(coverage_path, 'w') as f:
            json.dump(coverage, f, indent=2)
            
        return test_plan
