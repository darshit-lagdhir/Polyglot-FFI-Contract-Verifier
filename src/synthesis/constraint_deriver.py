"""
Constraint Deriver
Implements the core logic for deriving semantic constraints from IR.
"""

from typing import List, Dict, Any, Optional
from .naming_convention_analyzer import NamingConventionAnalyzer
from .conservative_defaults import ConservativeDefaultPolicy
from .constraint_id_generator import ConstraintIDGenerator
from .synthesis_warnings import SynthesisWarningLogger

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
