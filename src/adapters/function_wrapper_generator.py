"""
Function Wrapper Generator
Generates contract-enforcing Python wrappers for native functions.
"""

from typing import Dict, Any, List
from .constraint_enforcement_codegen import ConstraintEnforcementCodegen

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
        from .struct_definition_generator import StructDefinitionGenerator
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
