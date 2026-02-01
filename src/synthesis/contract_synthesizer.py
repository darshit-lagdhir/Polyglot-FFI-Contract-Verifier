"""
Contract Synthesizer
Orchestrates the transformation of IR into a formal FFI Contract.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any

from src.core.execution_context import ExecutionContext
from .constraint_deriver import ConstraintDeriver
from .synthesis_warnings import SynthesisWarningLogger
from .constraint_id_generator import ConstraintIDGenerator

class ContractSynthesizer:
    """
    Main engine for . Synthesizes semantic constraints from normalized IR.
    """
    
    def __init__(self):
        self.logger = SynthesisWarningLogger()
        self.deriver = ConstraintDeriver(self.logger)
        self.id_gen = ConstraintIDGenerator()

    def synthesize(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Synthesize the contract from IR.
        """
        ir_path = context.artifacts.intermediate_representation_path
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}. Run  first.")
            
        with open(ir_path, "r") as f:
            ir = json.load(f)
            
        type_registry = ir.get("type_registry", {})
        
        # 1. Synthesize Function Contracts
        function_contracts = self._synthesize_functions(ir.get("functions", []), type_registry)
        
        # 2. Synthesize Struct Contracts
        struct_contracts = self._synthesize_structs(ir.get("structs", []), type_registry)
        
        # 3. Apply Global Constraints (Rules 7, 8, 32/64 bit consistency)
        global_constraints = self._generate_global_constraints(context)
        
        # 4. Compile Metadata
        metadata = {
            "total_functions_analyzed": len(ir.get("functions", [])),
            "total_structs_analyzed": len(ir.get("structs", [])),
            "total_constraints_generated": self._count_constraints(function_contracts, struct_contracts, global_constraints),
            "warnings_issued": len(self.logger.get_all()),
            "synthesis_warnings": self.logger.get_all()
        }
        
        # 5. Build Final Artifact
        contract = {
            "provenance": {
                "producing_phase": ": Contract Synthesis",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(ir_path)]
            },
            "platform": ir.get("platform", {}),
            "function_contracts": function_contracts,
            "struct_contracts": struct_contracts,
            "type_contracts": self._synthesize_type_contracts(type_registry),
            "global_constraints": global_constraints,
            "synthesis_metadata": metadata
        }
        
        # 6. Save Artifact
        output_path = context.artifacts.contract_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(contract, f, indent=2)
            
        return contract

    def _synthesize_functions(self, functions: List[Dict[str, Any]], type_registry: Dict) -> List[Dict[str, Any]]:
        contracts = []
        for func in functions:
            name = func["name"]
            
            # Parameter Contracts
            param_contracts = []
            pre_conditions = []
            
            for param in func.get("parameters", []):
                p_contract = self.deriver.derive_parameter_contract(name, param)
                param_contracts.append(p_contract)
                
                # Turn specific semantic properties into explicit pre-conditions
                p_name = param["name"]
                if p_contract["nullability"] == "non_null":
                    pre_conditions.append({
                        "constraint_id": self.id_gen.generate_function_id(name, f"p_{p_name}", "non_null"),
                        "constraint_type": "non_null",
                        "description": f"Parameter '{p_name}' must not be NULL",
                        "target": f"parameter:{p_name}",
                        "justification": p_contract["nullability_justification"],
                        "severity": "error"
                    })
                
                # Rule 8 check (indirectly via type_id layout)
                if "struct:" in p_contract["type_id"]:
                    struct_id = p_contract["type_id"].split("pointer:")[-1] if "pointer:" in p_contract["type_id"] else p_contract["type_id"]
                    if struct_id in type_registry:
                        s_info = type_registry[struct_id]
                        pre_conditions.append({
                            "constraint_id": self.id_gen.generate_function_id(name, f"p_{p_name}", "layout_valid"),
                            "constraint_type": "struct_layout",
                            "description": f"Parameter '{p_name}' must point to valid memory matching {struct_id}",
                            "target": f"parameter:{p_name}",
                            "struct_type_id": struct_id,
                            "required_size_bytes": s_info.get("size_bytes"),
                            "required_alignment_bytes": s_info.get("alignment_bytes"),
                            "justification": "Type signature requires specific binary layout",
                            "severity": "error"
                        })

            # Rule 4: Buffer Relationships
            pre_conditions.extend(self.deriver.derive_buffer_constraints(name, func.get("parameters", [])))
            
            # Return Contract
            ret_contract = self.deriver.derive_return_contract(name, func.get("return_type_id", ""))
            post_conditions = []
            for c in ret_contract["constraints"]:
                 post_conditions.append({
                    "constraint_id": self.id_gen.generate_function_id(name, "ret", c["constraint_type"]),
                    "constraint_type": c["constraint_type"],
                    "description": c["description"],
                    "target": "return_value",
                    "justification": c["justification"],
                    "severity": "warning"
                })

            # Rule 10: Variadic
            if func.get("is_variadic"):
                self.logger.warn_variadic_function(name)

            contracts.append({
                "function_name": name,
                "source_location": func.get("source_location"),
                "calling_convention": func.get("calling_convention", "cdecl"),
                "pre_conditions": pre_conditions,
                "post_conditions": post_conditions,
                "parameter_contracts": param_contracts,
                "return_contract": ret_contract
            })
            
        return contracts

    def _synthesize_structs(self, structs: List[Dict[str, Any]], type_registry: Dict) -> List[Dict[str, Any]]:
        contracts = []
        for s in structs:
            name = s["name"]
            type_id = s.get("type_id")
            
            field_contracts = []
            for field in s.get("fields", []):
                if field.get("is_implicit"): continue
                field_contracts.append(self.deriver.derive_struct_field_contract(name, field))
                
            invariants = [
                {
                    "constraint_type": "layout_match",
                    "description": f"Target language struct must match native layout of '{name}' exactly",
                    "justification": "FFI requires binary layout compatibility",
                    "severity": "critical"
                },
                {
                    "constraint_type": "alignment",
                    "description": f"Struct '{name}' must be {s.get('alignment_bytes')}-byte aligned",
                    "required_alignment": s.get("alignment_bytes"),
                    "justification": "Compiler-enforced alignment must be preserved",
                    "severity": "error"
                }
            ]
            
            contracts.append({
                "struct_name": name,
                "type_id": type_id,
                "source_location": s.get("source_location"),
                "size_bytes": s.get("size_bytes"),
                "alignment_bytes": s.get("alignment_bytes"),
                "field_contracts": field_contracts,
                "invariants": invariants
            })
        return contracts

    def _synthesize_type_contracts(self, type_registry: Dict) -> Dict[str, Any]:
        contracts = {}
        for tid, info in type_registry.items():
            contracts[tid] = {
                "type_id": tid,
                "kind": info.get("kind"),
                "constraints": {} # Placeholder for future deep type analysis
            }
        return contracts

    def _generate_global_constraints(self, context: ExecutionContext) -> List[Dict[str, Any]]:
        return [
            {
                "constraint_id": self.id_gen.generate_global_id("abi_compatibility"),
                "constraint_type": "abi_compatibility",
                "description": "All structs must maintain ABI compatibility across compilation",
                "justification": f"Verification performed for {context.platform.os_name} {context.platform.architecture}",
                "severity": "error"
            },
            {
                "constraint_id": self.id_gen.generate_global_id("calling_convention"),
                "constraint_type": "calling_convention",
                "description": "All functions use cdecl unless explicitly specified",
                "justification": "Standard calling convention for C FFIs",
                "severity": "error"
            }
        ]

    def _count_constraints(self, funcs, structs, globals) -> int:
        count = len(globals)
        for f in funcs:
            count += len(f["pre_conditions"]) + len(f["post_conditions"])
        for s in structs:
            count += len(s["invariants"])
            for fc in f["field_contracts"] if "field_contracts" in f else []: # small bug fix: fc in s
                 count += len(fc.get("constraints", []))
        # better loop
        count = len(globals)
        for f in funcs:
            count += len(f["pre_conditions"]) + len(f["post_conditions"])
        for s in structs:
            count += len(s["invariants"])
            for fc in s["field_contracts"]:
                count += len(fc["constraints"])
        return count
