"""
Contract Synthesis Module

This module orchestrates the transformation of normalized IR into a formal FFI Contract.
It infers semantic constraints (ownership, nullability, buffer sizes) from C signatures
and naming conventions.

Consolidates:
- ContractSynthesizer: Main engine
- ConstraintDeriver: Rule engine for 10 FFI rules
- NamingConventionAnalyzer: Heuristics analyzer
- ConservativeDefaultPolicy: Safety defaults
- ConstraintIDGenerator: Deterministic IDs
- SynthesisWarningLogger: Logging for ambiguities

From original implementation:  (src/synthesis/)
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from .context import ExecutionContext

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class SynthesisWarningLogger:
    """
    Captures warnings when automated analysis falls back to conservative defaults
    or encounters ambiguous patterns.
    """
    
    def __init__(self):
        self.warnings: List[Dict[str, Any]] = []

    def log(self, category: str, message: str, severity: str = "warning", context: str = ""):
        """Add a warning to the list."""
        self.warnings.append({
            "category": category,
            "message": message,
            "severity": severity,
            "context": context
        })

    def warn_ambiguous_ownership(self, func_name: str, param_name: str):
        self.log(
            "OWNERSHIP_AMBIGUITY",
            f"Could not determine ownership for parameter '{param_name}' in '{func_name}'. Assuming borrowed.",
            "warning",
            func_name
        )

    def warn_missing_buffer_size(self, func_name: str, param_name: str):
        self.log(
            "BUFFER_SAFETY",
            f"Pointer parameter '{param_name}' in '{func_name}' appears to be a buffer but has no associated size parameter.",
            "error",
            func_name
        )

    def warn_variadic_function(self, func_name: str):
        self.log(
            "VARIADIC_LIMITATION",
            f"Function '{func_name}' is variadic. Full verification is not supported without manual format string validation.",
            "warning",
            func_name
        )

    def get_all(self) -> List[Dict[str, Any]]:
        return self.warnings

class ConstraintIDGenerator:
    """
    Ensures every constraint in the contract has a traceable, unique identifier.
    """
    
    def generate_function_id(self, func_name: str, target: str, constraint_type: str) -> str:
        """
        Generate ID for function-related constraints.
        Format: func_<name>_<target>_<type>
        """
        # Clean target name (e.g. parameter:cfg -> p_cfg)
        clean_target = target.replace("parameter:", "p_").replace("return_value", "ret")
        base = f"func_{func_name}_{clean_target}_{constraint_type}"
        return self._normalize(base)

    def generate_struct_id(self, struct_name: str, field_name: str, constraint_type: str) -> str:
        """
        Generate ID for struct-related constraints.
        Format: struct_<name>_<field>_<type>
        """
        base = f"struct_{struct_name}_{field_name}_{constraint_type}"
        return self._normalize(base)

    def generate_global_id(self, constraint_type: str) -> str:
        """
        Generate ID for global constraints.
        Format: global_<type>
        """
        return f"global_{constraint_type}"

    def _normalize(self, base_id: str) -> str:
        """Ensure IDs are valid identifiers and deduplicated locally if needed."""
        # In a real system we might append a hash of the justification if multiple
        # identical constraints exist, but for our v1.0, semantic names are better.
        return base_id.lower().replace(" ", "_").replace("*", "ptr")

class ConservativeDefaultPolicy:
    """
    Implements mandatory fallback policies to ensure safety over permissiveness.
    """
    
    @staticmethod
    def default_nullability() -> str:
        """DEFAULT POLICY 1: Pointers are required unless proven optional."""
        return "non_null"
        
    @staticmethod
    def default_ownership() -> str:
        """DEFAULT POLICY 2: Assume borrowed (caller keeps ownership)."""
        return "borrowed"
        
    @staticmethod
    def default_lifetime() -> str:
        """DEFAULT POLICY 3: Valid only during function call."""
        return "call_duration"
        
    @staticmethod
    def default_mutability(is_const: bool) -> str:
        """DEFAULT POLICY 4: Favor immutable if const, else mutable."""
        return "immutable" if is_const else "mutable"
        
    @staticmethod
    def default_buffer_safety() -> Dict[str, Any]:
        """DEFAULT POLICY 5: Buffers are high risk."""
        return {
            "is_fixed_size": False,
            "requires_validation": True,
            "severity": "warning"
        }
        
    @staticmethod
    def default_return_semantics(return_type_id: str) -> str:
        """DEFAULT POLICY 6: Integer returns are treated as error codes."""
        if return_type_id.startswith("primitive:int"):
            return "error_code"
        return "value"

class NamingConventionAnalyzer:
    """
    Analyzes C naming conventions to infer intent for nullability, ownership, etc.
    """
    
    def is_nullable_name(self, name: str) -> bool:
        """Rule 1: Detect nullability hints."""
        lower_name = name.lower()
        prefixes = ["optional_", "maybe_", "nullable_"]
        suffixes = ["_opt", "_nullable", "_maybe"]
        
        return any(lower_name.startswith(p) for p in prefixes) or \
               any(lower_name.endswith(s) for s in suffixes)

    def is_ownership_transfer_function(self, func_name: str) -> Optional[str]:
        """Rule 2: Detect ownership transfer intent."""
        lower_name = func_name.lower()
        
        # Transfers to Caller (Allocation)
        transfers_to_caller = ["create_", "alloc_", "new_", "init_", "clone_", "dup_"]
        if any(lower_name.startswith(p) for p in transfers_to_caller):
            return "caller"
            
        # Transfers to Callee (Deallocation/Take-ownership)
        transfers_to_callee = ["destroy_", "free_", "delete_", "release_", "sink_", "take_"]
        if any(lower_name.startswith(p) for p in transfers_to_callee):
            return "callee"
            
        return None

    def is_borrowed_function(self, func_name: str) -> bool:
        """Detect intent for non-transferring operations."""
        lower_name = func_name.lower()
        prefixes = ["get_", "find_", "query_", "peek_", "view_", "process_", "write_", "read_"]
        return any(lower_name.startswith(p) for p in prefixes)

    def detect_buffer_size_relationship(self, pointer_name: str, scalar_name: str) -> bool:
        """Rule 4: Detect relationship between a buffer and its size parameter."""
        p_name = pointer_name.lower()
        s_name = scalar_name.lower()
        
        # 1. Name match + size/len suffix
        size_indicators = ["_size", "_len", "_count", "_length", "size", "len", "count"]
        for indicator in size_indicators:
            if s_name == f"{p_name}{indicator}" or s_name == indicator:
                return True
                
        # 2. Heuristic for common pairs
        common_pairs = {
            "buffer": ["buffer_size", "buf_len", "size"],
            "data": ["data_size", "datalen", "len"],
            "items": ["count", "num_items"],
            "ptr": ["size", "count"]
        }
        
        if p_name in common_pairs and s_name in common_pairs[p_name]:
            return True
            
        return False

    def is_error_code_return(self, func_name: str, return_type_id: str) -> bool:
        """Rule 6: Detect if return value represents an error code."""
        if return_type_id not in ["primitive:int32", "primitive:int64", "primitive:int16"]:
            return False
            
        lower_name = func_name.lower()
        indicators = ["status", "error", "result", "code", "write", "process", "save", "init", "open"]
        return any(ind in lower_name for ind in indicators)

class ConstraintDeriver:
    """
    Applies derivation rules to functions, parameters, and structs.
    """
    
    def __init__(self, warning_logger: SynthesisWarningLogger):
        self.naming_analyzer = NamingConventionAnalyzer()
        self.defaults = ConservativeDefaultPolicy()
        self.id_gen = ConstraintIDGenerator()
        self.logger = warning_logger

    def derive_parameter_contract(self, func_name: str, param: Dict[str, Any]) -> Dict[str, Any]:
        """derive rules 1, 2, 3, 4, 9 for a parameter."""
        p_name = param.get("name")
        p_type_id = param.get("type_id", "")
        is_pointer = p_type_id.startswith("pointer:")
        is_const = param.get("qualifiers", {}).get("is_const", False)
        
        # Rule 1: Nullability
        nullability = self.defaults.default_nullability()
        null_just = "Pointer parameter without indication of nullability"
        
        if is_pointer:
            if self.naming_analyzer.is_nullable_name(p_name):
                nullability = "nullable"
                null_just = "Naming convention suggests optional parameter"
        else:
            nullability = "not_applicable"
            null_just = "Non-pointer value"

        # Rule 2: Ownership
        ownership = self.defaults.default_ownership()
        own_just = "No indication of ownership transfer; assumed borrowed"
        
        if is_pointer:
            transfer_intent = self.naming_analyzer.is_ownership_transfer_function(func_name)
            if transfer_intent == "callee" and not is_const:
                # If function is 'destroy_config(Config* cfg)', cfg is transferred
                ownership = "transferred"
                own_just = "Function naming suggests callee takes ownership"
            elif transfer_intent == "caller":
                # This usually applies to return values, but parameters in 'init' might be borrowed
                pass
            
            if ownership == self.defaults.default_ownership() and not self.naming_analyzer.is_borrowed_function(func_name):
                # We couldn't find a strong rule, so we used default. Log it.
                self.logger.warn_ambiguous_ownership(func_name, p_name)

        # Rule 3: Lifetime
        lifetime = self.defaults.default_lifetime()
        life_just = "Borrowed pointer valid only during call"
        if ownership == "transferred":
            lifetime = "transferred_to_callee"
            life_just = "Ownership transferred to callee"

        # Rule 9: Mutability
        mutability = self.defaults.default_mutability(is_const)
        mut_just = "Const qualifier prohibits modification" if is_const else "No const qualifier; assume mutable"

        # Construct constraints list
        constraints = []
        if is_pointer:
            constraints.append({
                "constraint_type": "valid_pointer",
                "description": "Must point to valid memory"
            })
            if "pointer:primitive:" not in p_type_id: # likely struct or complex
                constraints.append({
                    "constraint_type": "alignment",
                    "description": "Must be properly aligned for its type"
                })

        return {
            "parameter_name": p_name,
            "type_id": p_type_id,
            "nullability": nullability,
            "nullability_justification": null_just,
            "ownership": ownership,
            "ownership_justification": own_just,
            "lifetime": lifetime,
            "lifetime_justification": life_just,
            "mutability": mutability,
            "mutability_justification": mut_just,
            "constraints": constraints
        }

    def derive_buffer_constraints(self, func_name: str, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rule 4: Detect buffer-length pairs."""
        constraints = []
        
        for i, p1 in enumerate(parameters):
            p1_name = p1.get("name")
            p1_type = p1.get("type_id", "")
            
            if not p1_type.startswith("pointer:"):
                continue
                
            found_size = False
            for j, p2 in enumerate(parameters):
                if i == j: continue
                
                p2_name = p2.get("name")
                p2_type = p2.get("type_id", "")
                
                if p2_type.startswith("primitive:int") or p2_type.startswith("primitive:uint"):
                    if self.naming_analyzer.detect_buffer_size_relationship(p1_name, p2_name):
                        constraints.append({
                            "constraint_id": self.id_gen.generate_function_id(func_name, f"p_{p1_name}", "buffer_relationship"),
                            "constraint_type": "buffer_size",
                            "description": f"Parameter '{p1_name}' buffer size is defined by '{p2_name}'",
                            "target": f"parameter:{p1_name}",
                            "size_parameter": p2_name,
                            "justification": f"Naming relationship between '{p1_name}' and '{p2_name}'",
                            "severity": "error"
                        })
                        found_size = True
            
            # Special Rule for char*
            if p1_type == "pointer:primitive:char" and not found_size:
                 constraints.append({
                    "constraint_id": self.id_gen.generate_function_id(func_name, f"p_{p1_name}", "string_null_terminated"),
                    "constraint_type": "null_terminated_string",
                    "description": f"Parameter '{p1_name}' must be a null-terminated string",
                    "target": f"parameter:{p1_name}",
                    "justification": "C convention for char* parameters",
                    "severity": "error"
                })
            elif p1_type == "pointer:primitive:void" and not found_size:
                self.logger.warn_missing_buffer_size(func_name, p1_name)

        return constraints

    def derive_return_contract(self, func_name: str, return_type_id: str) -> Dict[str, Any]:
        """Rule 6: Return value intent."""
        ownership = "value"
        own_just = "Returned by value"
        
        constraints = []
        
        if return_type_id.startswith("pointer:"):
            transfer_intent = self.naming_analyzer.is_ownership_transfer_function(func_name)
            if transfer_intent == "caller":
                ownership = "transferred"
                own_just = "Function naming suggests caller takes ownership of returned pointer"
            else:
                ownership = "borrowed"
                own_just = "Assume returned pointer is borrowed from internal state"
        
        # Error code detection
        if self.naming_analyzer.is_error_code_return(func_name, return_type_id):
            constraints.append({
                "constraint_type": "error_code",
                "description": "Returns 0 on success, non-zero on failure",
                "justification": "Naming and return type suggest error code pattern"
            })
            
        return {
            "type_id": return_type_id,
            "ownership": ownership,
            "ownership_justification": own_just,
            "constraints": constraints
        }

    def derive_struct_field_contract(self, struct_name: str, field: Dict[str, Any]) -> Dict[str, Any]:
        """Rule 5: Struct field constraints."""
        name = field.get("name")
        type_id = field.get("type_id", "")
        
        constraints = []
        if "padding" not in type_id:
            constraints.append({
                "constraint_type": "initialized",
                "description": "Must be initialized before use"
            })
            
        nullability = "not_applicable"
        if type_id.startswith("pointer:"):
            # Struct fields are often NULL unless specifically used for sub-objects
             nullability = "nullable"
             constraints.append({
                 "constraint_type": "nullable_pointer",
                 "description": "May be NULL"
             })

        return {
            "field_name": name,
            "type_id": type_id,
            "offset_bytes": field.get("offset_bytes"),
            "nullability": nullability,
            "ownership": "unknown",
            "constraints": constraints
        }

# ============================================================================
# PUBLIC API
# ============================================================================

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
            for fc in s["field_contracts"]:
                 count += len(fc.get("constraints", []))
        return count
