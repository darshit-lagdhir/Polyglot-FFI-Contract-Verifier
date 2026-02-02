"""
Test Planning Module

This module orchestrates the creation of exhaustive test suites from FFI contracts.
It generates positive, negative, and boundary test cases to verify contract constraints.

Consolidates:
- TestPlanGenerator: Main orchestrator
- InputValueGenerator: Produces deterministic input values
- PositiveTestGenerator: Generates valid test cases
- NegativeTestGenerator: Generates constraint violation cases
- BoundaryValueTestGenerator: Generates edge case tests
- CoverageAnalyzer: Tracks constraint coverage

From original implementation: Phase 7 (src/testing/)
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class InputValueGenerator:
    """
    Deterministic generation of input values for FFI tests.
    """
    
    PRIMITIVE_VALUES = {
        "primitive:int8": [1, 127, -128],
        "primitive:int16": [1, 32767, -32768],
        "primitive:int32": [42, 2147483647, -2147483648],
        "primitive:int64": [100, 9223372036854775807, -9223372036854775808],
        "primitive:uint8": [1, 255, 0],
        "primitive:uint16": [1, 65535, 0],
        "primitive:uint32": [100, 4294967295, 0],
        "primitive:uint64": [1000, 18446744073709551615, 0],
        "primitive:float": [1.0, 3.14159, 1.175494e-38],
        "primitive:double": [1.0, 3.1415926535, 2.225073e-308],
        "primitive:char": ["A", "Z", "\0"],
        "primitive:bool": [True, False],
        "primitive:void": [None]
    }

    def generate_value(self, type_id: str, ir: Dict[str, Any], strategy: str = "typical") -> Any:
        """
        Generates a concrete value for a given type.
        
        Strategies:
            - minimal: Smallest valid value
            - typical: Average/common value
            - maximal: Largest valid value
        """
        idx = {"minimal": 0, "typical": 0, "maximal": 1 if "int" in type_id else 0}.get(strategy, 0)
        
        # Handle primitives
        if type_id in self.PRIMITIVE_VALUES:
            vals = self.PRIMITIVE_VALUES[type_id]
            if strategy == "maximal" and len(vals) > 1: return vals[1]
            if strategy == "minimal" and len(vals) > 2: return vals[2]
            return vals[0]

        # Handle pointers
        if type_id.startswith("pointer:"):
            if strategy == "minimal": return None
            base_type = type_id.replace("pointer:", "")
            
            if base_type == "primitive:char":
                return "test_string\0"
            if base_type.startswith("struct:"):
                struct_name = base_type.split(":")[-1]
                return self.generate_struct_value(struct_name, ir, strategy)
            
            # Default for pointers is a small buffer or null
            return {"type": "buffer", "size": 8, "data": [0] * 8}

        # Handle structs (inline)
        if type_id.startswith("struct:"):
            return self.generate_struct_value(type_id.split(":")[-1], ir, strategy)

        return 0

    def generate_struct_value(self, struct_name: str, ir: Dict[str, Any], strategy: str = "typical") -> Dict[str, Any]:
        """Generates a valid dictionary representation of a struct."""
        # Find struct in IR
        struct_def = None
        for s in ir.get("structs", []):
            if s["name"] == struct_name:
                struct_def = s
                break
        
        if not struct_def:
            return {}

        value = {}
        for field in struct_def.get("fields", []):
            if field.get("is_padding"):
                continue
            f_name = field["name"]
            f_type = field["type_id"]
            value[f_name] = self.generate_value(f_type, ir, strategy)
            
        return value


class PositiveTestGenerator:
    """
    Produces successful execution test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_positive_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates a set of positive test cases for a function."""
        name = f_contract["function_name"]
        test_cases = []
        
        # 1. Minimal Valid
        test_cases.append(self._create_test_case(f_contract, ir, "minimal"))
        
        # 2. Typical Valid
        test_cases.append(self._create_test_case(f_contract, ir, "typical"))
        
        return test_cases

    def _create_test_case(self, f: Dict[str, Any], ir: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        params = {}
        for p in f.get("parameter_contracts", []):
            params[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, strategy)
            }
            
        cids = [pc["constraint_id"] for pc in f.get("pre_conditions", [])]
        
        return {
            "test_id": f"test_{f['function_name']}_positive_{strategy}",
            "test_category": "positive",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Valid call to {f['function_name']} with {strategy} inputs",
            "constraints_exercised": cids,
            "inputs": params,
            "expected_outcome": {
                "type": "success",
                "return_value_type": f.get("return_contract", {}).get("type_id", "primitive:void")
            },
            "rationale": f"Verifies that valid {strategy} inputs are accepted."
        }


class NegativeTestGenerator:
    """
    Produces failure execution test cases for constraint verification.
    """
    
    EXCEPTION_MAP = {
        "non_null": "NullPointerViolation",
        "buffer_size": "BufferSizeViolation",
        "struct_layout": "LayoutMismatchError",
        "alignment": "LayoutMismatchError",
        "borrowed": "OwnershipViolation",
        "transferred": "OwnershipViolation",
        "error_code": "ReturnValueViolation",
        "null_terminated_string": "FFIContractViolation"
    }
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_negative_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates one negative test case per pre-condition."""
        test_cases = []
        name = f_contract["function_name"]
        
        for constraint in f_contract.get("pre_conditions", []):
            tc = self._generate_violation(f_contract, constraint, ir)
            if tc:
                 test_cases.append(tc)
                 
        return test_cases

    def _generate_violation(self, f: Dict[str, Any], c: Dict[str, Any], ir: Dict[str, Any]) -> Dict[str, Any]:
        c_type = c["constraint_type"]
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        
        # Start with typical valid inputs
        inputs = {}
        for p in f.get("parameter_contracts", []):
            p_name = p["parameter_name"]
            inputs[p_name] = {
                "type": p["type_id"],
                "value": self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        # Corrupt the target input based on constraint type
        exc_type = self.EXCEPTION_MAP.get(c_type, "FFIContractViolation")
        
        if c_type == "non_null":
            if target in inputs:
                inputs[target]["value"] = None
            else:
                return None # Target not found
        
        elif c_type == "buffer_size":
            size_param = c.get("size_parameter")
            if size_param in inputs:
                inputs[size_param]["value"] = -1 # Invalid size
            else:
                 pass

        elif c_type == "struct_layout":
            if target in inputs:
                 # Injected layout error
                 inputs[target]["size_override"] = c.get("required_size_bytes", 100) + 1
            else:
                return None

        elif c_type == "null_terminated_string":
            if target in inputs:
                 inputs[target]["value"] = "not_terminated" # Missing \0
            else:
                return None

        else:
            return None # Unsupported for now

        return {
            "test_id": f"test_{f['function_name']}_violate_{cid}",
            "test_category": "negative",
            "priority": "critical" if c_type in ["non_null", "buffer_size"] else "high",
            "function_name": f["function_name"],
            "description": f"Violate constraint {cid} ({c_type}) for {target}",
            "constraints_exercised": [cid],
            "inputs": inputs,
            "expected_outcome": {
                "type": "exception",
                "exception_type": exc_type,
                "constraint_id": cid,
                "message_pattern": c.get("description", "")
            },
            "rationale": f"Verifies that {c_type} protection is active."
        }


class BoundaryValueTestGenerator:
    """
    Produces edge case test cases.
    """
    
    def __init__(self, input_gen: InputValueGenerator):
        self.input_gen = input_gen

    def generate_boundary_tests(self, f_contract: Dict[str, Any], ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates boundary tests for relevant parameters."""
        test_cases = []
        
        for p in f_contract.get("parameter_contracts", []):
            t_id = p["type_id"]
            if "int" in t_id or "uint" in t_id:
                # Add Zero Test
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "zero", 0))
                # Add Max Test
                max_val = self.input_gen.generate_value(t_id, ir, "maximal")
                test_cases.append(self._create_boundary_test(f_contract, ir, p["parameter_name"], "max", max_val))
                
        return test_cases

    def _create_boundary_test(self, f: Dict[str, Any], ir: Dict[str, Any], p_name: str, b_type: str, val: Any) -> Dict[str, Any]:
        inputs = {}
        for p in f.get("parameter_contracts", []):
            inputs[p["parameter_name"]] = {
                "type": p["type_id"],
                "value": val if p["parameter_name"] == p_name else self.input_gen.generate_value(p["type_id"], ir, "typical")
            }
            
        return {
            "test_id": f"test_{f['function_name']}_boundary_{p_name}_{b_type}",
            "test_category": "boundary",
            "priority": "normal",
            "function_name": f["function_name"],
            "description": f"Boundary test ({b_type}) for parameter {p_name}",
            "constraints_exercised": [], # Exercised implicitly
            "inputs": inputs,
            "expected_outcome": {
                "type": "success"
            },
            "rationale": f"Checks handling of {b_type} boundary for {p_name}."
        }


class CoverageAnalyzer:
    """
    Computes coverage statistics for a generated test plan.
    """
    
    def analyze_coverage(self, test_cases: List[Dict[str, Any]], contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes which constraints are covered by the test cases.
        """
        all_constraints = self._extract_all_constraints(contract)
        coverage_map = {cid: [] for cid in all_constraints}
        
        for tc in test_cases:
            for cid in tc.get("constraints_exercised", []):
                if cid in coverage_map:
                    coverage_map[cid].append(tc["test_id"])

        covered_count = sum(1 for cid in coverage_map if len(coverage_map[cid]) > 0)
        total_count = len(all_constraints)
        
        uncovered = [cid for cid in coverage_map if len(coverage_map[cid]) == 0]
        
        return {
            "summary": {
                "total_constraints": total_count,
                "covered_constraints": covered_count,
                "uncovered_constraints": len(uncovered),
                "coverage_percentage": (covered_count / total_count * 100.0) if total_count > 0 else 100.0
            },
            "coverage_map": coverage_map,
            "uncovered_constraints": uncovered
        }

    def _extract_all_constraints(self, contract: Dict[str, Any]) -> List[str]:
        """Extracts every unique constraint ID from the contract."""
        ids = set()
        for f in contract.get("function_contracts", []):
            for pc in f.get("pre_conditions", []):
                 ids.add(pc["constraint_id"])
            for pc in f.get("post_conditions", []):
                 ids.add(pc["constraint_id"])
        return sorted(list(ids))


# ============================================================================
# PUBLIC API
# ============================================================================

class TestPlanGenerator:
    """
    Main orchestrator for Phase 7.
    Generates a complete test plan based on the contract and IR.
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
