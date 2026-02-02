"""
Adapter Generation Module

This module handles the generation of Python language adapters, including ctypes structures,
exception hierarchies, and function wrappers with constraint enforcement.

Consolidates:
- AdapterGenerator
- StructDefinitionGenerator
- FunctionWrapperGenerator
- ExceptionClassGenerator
- OwnershipTrackerGenerator
- ConstraintEnforcementCodegen

From original implementation:  (src/adapters/)
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class ExceptionClassGenerator:
    """
    Produces the Python code for the exceptions module in the generated adapter.
    """
    
    def generate_exception_module(self, library_name: str) -> str:
        """Generates the full source code for the exceptions module."""
        return f'''"""
Generated exception classes for {library_name}.

Auto-created by Polyglot FFI Contract Verifier.
DO NOT EDIT MANUALLY.
"""

class FFIContractViolation(Exception):
    """
    Base class for all FFI contract violations.
    
    Attributes:
        constraint_id: Unique identifier for the violated constraint
        message: Human-readable description of the violation
    """
    def __init__(self, constraint_id, message):
        self.constraint_id = constraint_id
        self.message = message
        super().__init__(f"[{{constraint_id}}] {{message}}")

class NullPointerViolation(FFIContractViolation):
    """
    Raised when a pointer that must not be NULL is actually NULL.
    
    Contract constraint type: non_null
    """
    pass

class BufferSizeViolation(FFIContractViolation):
    """
    Raised when a buffer size constraint is violated.
    
    Contract constraint type: buffer_size
    """
    pass

class LayoutMismatchError(FFIContractViolation):
    """
    Raised when a struct layout doesn't match the contract specification.
    
    Contract constraint type: struct_layout
    """
    pass

class OwnershipViolation(FFIContractViolation):
    """
    Raised when memory ownership rules are violated.
    
    Contract constraint types: borrowed, transferred
    """
    pass

class ReturnValueViolation(FFIContractViolation):
    """
    Raised when a return value doesn't satisfy post-conditions.
    
    Contract constraint type: error_code, return_value_range
    """
    pass
'''

class OwnershipTrackerGenerator:
    """
    Produces the Python code for the ownership tracker in the generated adapter.
    """
    
    def generate_ownership_module(self, library_name: str) -> str:
        """Generates the full source code for the ownership tracking module."""
        return f'''"""
Generated ownership tracker for {library_name}.

Auto-created by Polyglot FFI Contract Verifier.
DO NOT EDIT MANUALLY.
"""

import weakref
from . import {library_name}_exceptions as exceptions

class OwnershipTracker:
    """
    Tracks memory ownership across the FFI boundary.
    
    Detects:
      - Use-after-transfer (using pointer after ownership was transferred)
      - Double-transfer (transferring ownership of same pointer twice)
    """
    
    def __init__(self):
        self._borrowed_pointers = weakref.WeakSet()
        self._transferred_pointers = set()
    
    def mark_borrowed(self, ptr):
        """
        Mark a pointer as borrowed (caller retains ownership).
        """
        if ptr is not None and bool(ptr):
            # We track the ID of the object if possible, 
            # or the address for pointer types
            try:
                import ctypes
                if isinstance(ptr, (ctypes._Pointer, ctypes.c_void_p)):
                    addr = ctypes.addressof(ptr.contents) if hasattr(ptr, 'contents') else ptr.value
                    self._borrowed_pointers.add(addr)
                else:
                    self._borrowed_pointers.add(id(ptr))
            except:
                self._borrowed_pointers.add(id(ptr))
    
    def mark_transferred(self, ptr):
        """
        Mark a pointer as transferred (callee takes ownership).
        """
        if ptr is None or not bool(ptr):
            return
            
        ptr_id = id(ptr)
        if ptr_id in self._transferred_pointers:
            raise exceptions.OwnershipViolation(
                "ownership_double_transfer",
                f"Pointer {{hex(ptr_id)}} has already been transferred"
            )
        
        self._transferred_pointers.add(ptr_id)
        
    def check_valid(self, ptr):
        """
        Check if a pointer is still valid to use.
        """
        if ptr is None or not bool(ptr):
            return
            
        ptr_id = id(ptr)
        if ptr_id in self._transferred_pointers:
            raise exceptions.OwnershipViolation(
                "ownership_use_after_transfer",
                f"Pointer {{hex(ptr_id)}} was transferred and is no longer valid"
            )

# Global tracker instance
_tracker = OwnershipTracker()
'''

class StructDefinitionGenerator:
    """
    Produces Python ctypes Structure definitions from contract/IR data.
    """
    
    TYPE_MAP = {
        "primitive:int8": "ctypes.c_int8",
        "primitive:int16": "ctypes.c_int16",
        "primitive:int32": "ctypes.c_int32",
        "primitive:int64": "ctypes.c_int64",
        "primitive:uint8": "ctypes.c_uint8",
        "primitive:uint16": "ctypes.c_uint16",
        "primitive:uint32": "ctypes.c_uint32",
        "primitive:uint64": "ctypes.c_uint64",
        "primitive:float": "ctypes.c_float",
        "primitive:double": "ctypes.c_double",
        "primitive:char": "ctypes.c_char",
        "primitive:void": "None",
        "pointer:primitive:void": "ctypes.c_void_p",
        "pointer:primitive:char": "ctypes.c_char_p"
    }
    
    def generate_struct_module(self, library_name: str, structs: List[Dict[str, Any]], ir: Dict[str, Any]) -> str:
        """Generates the full structs module."""
        lines = [
            f'"""',
            f'Generated struct definitions for {library_name}.',
            f'',
            f'Auto-created by Polyglot FFI Contract Verifier.',
            f'DO NOT EDIT MANUALLY.',
            f'"""',
            f'',
            f'import ctypes',
            f'from . import {library_name}_exceptions as exceptions',
            f''
        ]
        
        # We need to sort structs by dependency if they nest, 
        # but for v1.0 we assume flat or pre-ordered
        for s in structs:
            lines.append(self.generate_struct_class(s))
            lines.append("")
            
        return "\n".join(lines)

    def generate_struct_class(self, s: Dict[str, Any]) -> str:
        name = s["struct_name"]
        size = s["size_bytes"]
        align = s["alignment_bytes"]
        
        fields = s.get("field_contracts", [])
        
        class_lines = [
            f"class {name}(ctypes.Structure):",
            f'    """',
            f'    Native struct \'{name}\' binding.',
            f'    Size: {size} bytes',
            f'    Alignment: {align} bytes',
            f'    """',
            f'    _fields_ = ['
        ]
        
        for f in fields:
            f_name = f["field_name"]
            f_type = f["type_id"]
            ctypes_type = self._map_type(f_type)
            class_lines.append(f'        ("{f_name}", {ctypes_type}),')
            
        class_lines.extend([
            f'    ]',
            f'',
            f'    def __init__(self, **kwargs):',
            f'        super().__init__()',
            f'        actual_size = ctypes.sizeof(self)',
            f'        if actual_size != {size}:',
            f'            raise exceptions.LayoutMismatchError(',
            f'                "struct:{name}",',
            f'                f"Struct {name} has size {{actual_size}} bytes, expected {size} bytes"',
            f'            )',
            f'        for key, value in kwargs.items():',
            f'            if not hasattr(self, key):',
            f'                raise ValueError(f"Unknown field: {{key}}")',
            f'            setattr(self, key, value)',
            f'            setattr(self, key, value)',
            f''
        ])
        
        return "\n".join(class_lines)

    def _map_type(self, type_id: str) -> str:
        if type_id in self.TYPE_MAP:
            return self.TYPE_MAP[type_id]
            
        if type_id.startswith("padding:"):
            size = type_id.split(":")[-1]
            return f"ctypes.c_byte * {size}"
            
        if type_id.startswith("pointer:struct:"):
            s_name = type_id.split(":")[-1]
            return f"ctypes.POINTER({s_name})"
            
        if type_id.startswith("struct:"):
            return type_id.split(":")[-1]
            
        if type_id.startswith("pointer:primitive:"):
             base = type_id.replace("pointer:", "")
             if base in self.TYPE_MAP:
                 return f"ctypes.POINTER({self.TYPE_MAP[base]})"
                 
        return "ctypes.c_void_p" # Fallback

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

class FunctionWrapperGenerator:
    """
    Produces Python wrapper functions with pre/post-condition checks.
    """
    
    def __init__(self):
        self.codegen = ConstraintEnforcementCodegen()
        
    def generate_wrapper_module(self, library_name: str, library_path: str, functions: List[Dict[str, Any]]) -> str:
        """Generates the main adapter module."""
        lines = [
            f'"""',
            f'Generated FFI adapter for {library_name}.',
            f'Auto-created by Polyglot FFI Contract Verifier.',
            f'"""',
            f'',
            f'import ctypes',
            f'import os',
            f'from . import {library_name}_structs as structs',
            f'from . import {library_name}_exceptions as exceptions',
            f'from . import {library_name}_ownership as ownership',
            f'',
            f'_LIBRARY_PATH = r"{library_path}"',
            f'if not os.path.exists(_LIBRARY_PATH):',
            f'    raise FileNotFoundError(f"Native library not found: {{_LIBRARY_PATH}}")',
            f'',
            f'_lib = ctypes.CDLL(_LIBRARY_PATH)',
            f''
        ]
        
        # Configure signatures first
        for f in functions:
            lines.append(self._generate_signature_config(f))
            
        lines.append("")
        
        # Then generate wrappers
        for f in functions:
            lines.append(self.generate_wrapper(f))
            lines.append("")
            
        return "\n".join(lines)

    def _generate_signature_config(self, f: Dict[str, Any]) -> str:
        name = f["function_name"]
        argtypes = [self._map_type(p["type_id"]) for p in f.get("parameter_contracts", [])]
        restype = self._map_type(f.get("return_contract", {}).get("type_id", "primitive:void"))
        
        lines = []
        if any(at == "NOT_FOUND" for at in argtypes + [restype]):
             lines.append(f"# Warning: Could not fully resolve types for {name}")
             
        lines.append(f"_lib.{name}.argtypes = [{', '.join([at for at in argtypes if at != 'NOT_FOUND'])}]")
        lines.append(f"_lib.{name}.restype = {restype if restype != 'NOT_FOUND' else 'None'}")
        
        if f.get("calling_convention") == "stdcall":
             lines.append(f"# Important: stdcall is handled by WinDLL if needed, currently using default CDLL")
             
        return "\n".join(lines)

    def generate_wrapper(self, f: Dict[str, Any]) -> str:
        name = f["function_name"]
        params = f.get("parameter_contracts", [])
        param_names = [p["parameter_name"] for p in params]
        
        lines = [
            f"def {name}({', '.join(param_names)}):",
            f'    """Wrapper for native function \'{name}\'."""'
        ]
        
        # Ownership tracking (Pre-call)
        for p in params:
            check = self.codegen.generate_ownership_check(p)
            if check: lines.append(check)
            
        # Pre-condition checks
        pre_conds = f.get("pre_conditions", [])
        if pre_conds:
            lines.append(f"    # Pre-conditions")
            for c in pre_conds:
                lines.append(self.codegen.generate_constraint_check(c))
                
        # Call
        lines.append(f"    result = _lib.{name}({', '.join(param_names)})")
        
        # Post-condition checks
        post_conds = f.get("post_conditions", [])
        if post_conds:
            lines.append(f"    # Post-conditions")
            for c in post_conds:
                lines.append(self.codegen.generate_constraint_check(c))
                
        lines.append("    return result")
        
        return "\n".join(lines)

    def _map_type(self, type_id: str) -> str:
        # Reuse mapping logic
        gen = StructDefinitionGenerator()
        res = gen._map_type(type_id)
        if res == type_id.split(":")[-1]: # it's a struct name
             return f"structs.{res}"
        if "POINTER(" in res:
             # handle POINTER(Config) -> POINTER(structs.Config)
             if "POINTER(structs." not in res and "POINTER(ctypes." not in res:
                  res = res.replace("POINTER(", "ctypes.POINTER(structs.")
             else:
                  res = res.replace("POINTER(", "ctypes.POINTER(")
        return res

# ============================================================================
# PUBLIC API
# ============================================================================

class AdapterGenerator:
    """
    Main orchestrator for .
    Generates the full suite of Python adapters.
    """
    
    def __init__(self):
        self.struct_gen = StructDefinitionGenerator()
        self.func_gen = FunctionWrapperGenerator()
        self.exc_gen = ExceptionClassGenerator()
        self.own_gen = OwnershipTrackerGenerator()

    def generate(self, context) -> Dict[str, Any]:
        """
        Generates the full suite of Python adapters.
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

        lib_name = os.path.basename(context.native_library.library_path).split('.')[0]
        lib_path = context.native_library.library_path
        
        output_dir = os.path.join(context.artifacts.working_directory, "adapters")
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Generate Exceptions
        exc_code = self.exc_gen.generate_exception_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_exceptions.py"), "w") as f:
            f.write(exc_code)
            
        # 2. Generate Ownership Tracker
        own_code = self.own_gen.generate_ownership_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_ownership.py"), "w") as f:
            f.write(own_code)
            
        # 3. Generate Structs
        struct_code = self.struct_gen.generate_struct_module(lib_name, contract.get("struct_contracts", []), ir)
        with open(os.path.join(output_dir, f"{lib_name}_structs.py"), "w") as f:
            f.write(struct_code)
            
        # 4. Generate Main Adapter
        adapter_code = self.func_gen.generate_wrapper_module(lib_name, lib_path, contract.get("function_contracts", []))
        with open(os.path.join(output_dir, f"{lib_name}_adapter.py"), "w") as f:
            f.write(adapter_code)
            
        # 5. Generate __init__.py
        with open(os.path.join(output_dir, "__init__.py"), "w") as f:
            f.write(f"from . import {lib_name}_adapter as adapter\n")
            f.write(f"from . import {lib_name}_structs as structs\n")
            f.write(f"from . import {lib_name}_exceptions as exceptions\n")

        # 6. Generate Metadata
        metadata = {
            "provenance": {
                "producing_phase": ": Language Adapter Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(contract_path), os.path.abspath(ir_path)]
            },
            "target_language": "Python",
            "ffi_mechanism": "ctypes",
            "library_name": lib_name,
            "library_path": lib_path,
            "generated_modules": [
                f"adapters/{lib_name}_adapter.py",
                f"adapters/{lib_name}_structs.py",
                f"adapters/{lib_name}_exceptions.py",
                f"adapters/{lib_name}_ownership.py"
            ],
            "statistics": {
                "functions_wrapped": len(contract.get("function_contracts", [])),
                "structs_generated": len(contract.get("struct_contracts", [])),
                "constraints_enforced": self._count_constraints(contract),
                "constraints_skipped": 0
            }
        }
        
        metadata_path = os.path.join(output_dir, "adapter_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def _count_constraints(self, contract: Dict[str, Any]) -> int:
        count = 0
        for f in contract.get("function_contracts", []):
            count += len(f.get("pre_conditions", []))
            count += len(f.get("post_conditions", []))
        return count
