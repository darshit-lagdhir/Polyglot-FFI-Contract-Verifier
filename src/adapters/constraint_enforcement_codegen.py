"""
Constraint Enforcement Code Generator
Translates contract constraints into Python runtime checks.
"""

from typing import Dict, Any, List

class ConstraintEnforcementCodegen:
    """
    Generates Python logic for enforcing individual contract constraints.
    """
    
    def generate_constraint_check(self, constraint: Dict[str, Any]) -> str:
        """Dispatches to specific generator based on constraint type."""
        c_type = constraint.get("constraint_type")
        
        if c_type == "non_null":
            return self._generate_null_check(constraint)
        elif c_type == "buffer_size":
            return self._generate_buffer_size_check(constraint)
        elif c_type == "struct_layout":
            return self._generate_layout_check(constraint)
        elif c_type == "null_terminated_string":
            return self._generate_string_null_terminated_check(constraint)
        elif c_type == "error_code":
            return self._generate_error_code_check(constraint)
            
        return f"    # Skip: Unsupported constraint type '{c_type}'"

    def _generate_null_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        desc = c["description"]
        
        return f"""    # Enforce: {cid}
    if {target} is None or not bool({target}):
        raise exceptions.NullPointerViolation(
            "{cid}",
            "{desc}"
        )"""

    def _generate_buffer_size_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        size_param = c.get("size_parameter")
        cid = c["constraint_id"]
        
        if not size_param:
            return f"    # Advise: {cid} - Missing size parameter for buffer check"
            
        return f"""    # Enforce: {cid}
    if {target} is not None:
        if {size_param} < 0:
             raise exceptions.BufferSizeViolation(
                "{cid}",
                f"Buffer size '{size_param}' must be non-negative, got {{{size_param}}}"
            )"""

    def _generate_layout_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        struct_name = c["struct_type_id"].split(":")[-1]
        req_size = c.get("required_size_bytes")
        req_align = c.get("required_alignment_bytes")
        
        # We need to handle both the struct object and a pointer to it
        lines = [
            f"    # Enforce: {cid}",
            f"    if not isinstance({target}, structs.{struct_name}) and not hasattr({target}, '_type_'):",
            f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Parameter '{target}' must be of type {struct_name}, got {{type({target})}}\")"
        ]
        
        if req_size:
            lines.append(f"    actual_size_{target} = ctypes.sizeof({target}.contents) if hasattr({target}, 'contents') else ctypes.sizeof({target})")
            lines.append(f"    if actual_size_{target} != {req_size}:")
            lines.append(f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Struct {struct_name} has size {{actual_size_{target}}} bytes, expected {req_size}\")")
            
        if req_align:
            lines.append(f"    ptr_val_{target} = ctypes.addressof({target}.contents) if hasattr({target}, 'contents') else ctypes.addressof({target})")
            lines.append(f"    if ptr_val_{target} % {req_align} != 0:")
            lines.append(f"        raise exceptions.LayoutMismatchError(\"{cid}\", f\"Struct {struct_name} at {{hex(ptr_val_{target})}} is not {req_align}-byte aligned\")")
            
        return "\n".join(lines)

    def _generate_string_null_terminated_check(self, c: Dict[str, Any]) -> str:
        target = c["target"].split(":")[-1]
        cid = c["constraint_id"]
        
        return f"""    # Enforce: {cid}
    if {target} is None:
        raise exceptions.NullPointerViolation("{cid}", "Parameter '{target}' must not be NULL")
    
    _val_{target} = {target}
    if isinstance(_val_{target}, str):
        _val_{target} = _val_{target}.encode('utf-8')
        
    if not _val_{target}.endswith(b'\\x00'):
        raise exceptions.FFIContractViolation("{cid}", "Parameter '{target}' must be null-terminated")"""

    def _generate_error_code_check(self, c: Dict[str, Any]) -> str:
        # Usually applied to return values in post-conditions
        cid = c["constraint_id"]
        return f"""    # Enforce: {cid}
    # (Important: Result is checked by the caller or specialized checked function)"""
    
    def generate_ownership_check(self, param: Dict[str, Any]) -> str:
        """Generates ownership tracking code."""
        name = param.get("parameter_name")
        ownership = param.get("ownership")
        
        if ownership == "borrowed":
            return f"    ownership._tracker.mark_borrowed({name})"
        elif ownership == "transferred":
            return f"    ownership._tracker.mark_transferred({name})"
            
        return ""
