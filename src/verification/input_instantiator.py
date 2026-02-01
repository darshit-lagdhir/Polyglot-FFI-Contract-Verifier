"""
Input Instantiator
Converts declarative input specifications from the test plan into concrete Python/ctypes objects.
"""

import ctypes
import importlib
import os
import sys
from typing import Any, Dict, Optional

class InputInstantiator:
    """
    Transforms JSON-based values into ctypes instances for FFI calls.
    """
    
    PRIMITIVE_MAP = {
        "primitive:int8": ctypes.c_int8,
        "primitive:int16": ctypes.c_int16,
        "primitive:int32": ctypes.c_int32,
        "primitive:int64": ctypes.c_int64,
        "primitive:uint8": ctypes.c_uint8,
        "primitive:uint16": ctypes.c_uint16,
        "primitive:uint32": ctypes.c_uint32,
        "primitive:uint64": ctypes.c_uint64,
        "primitive:float": ctypes.c_float,
        "primitive:double": ctypes.c_double,
        "primitive:char": ctypes.c_char,
        "primitive:bool": ctypes.c_bool,
        "primitive:void": None
    }

    def __init__(self, lib_name: str):
        self.lib_name = lib_name
        self.structs_module = None
        
        # Add adapters dir to path for imports
        adapters_path = os.path.abspath("adapters")
        if adapters_path not in sys.path:
            sys.path.append(adapters_path)
            
        try:
            self.structs_module = __import__(f"{lib_name}_structs")
        except ImportError:
            pass

    def instantiate(self, spec: Dict[str, Any]) -> Any:
        """Main entry point for instantiation."""
        t_id = spec["type"]
        val = spec.get("value")
        
        if val is None:
            return None

        # Handle Primitives
        if t_id in self.PRIMITIVE_MAP:
            if t_id == "primitive:char" and isinstance(val, str):
                return self.PRIMITIVE_MAP[t_id](val.encode('ascii')[0])
            return self.PRIMITIVE_MAP[t_id](val)

        # Handle Pointers
        if t_id.startswith("pointer:"):
            base_type = t_id.replace("pointer:", "")
            
            # String special case
            if base_type == "primitive:char" and isinstance(val, str):
                return ctypes.c_char_p(val.encode('ascii'))
            
            # Buffer special case
            if isinstance(val, list):
                # Currently only supporting uint8 buffers in test plans
                arr_type = ctypes.c_uint8 * len(val)
                arr = arr_type(*val)
                return ctypes.cast(arr, ctypes.POINTER(ctypes.c_uint8))
                
            # Struct Pointer
            if base_type.startswith("struct:"):
                struct_name = base_type.split(":")[-1]
                struct_obj = self.instantiate_struct(struct_name, val)
                
                # Apply size override for negative tests if present in the spec
                if "size_override" in spec:
                    # Very advanced: creating an 'aliased' invalid size view
                    # For v1.0, we rely on the adapter's layout check being 
                    # triggerable by metadata manipulation or similar if needed.
                    # Actually, the adapter generator uses the metadata.
                    # But here we are instantiating.
                    pass
                
                return ctypes.pointer(struct_obj)

        # Handle Structs (inline)
        if t_id.startswith("struct:"):
            struct_name = t_id.split(":")[-1]
            return self.instantiate_struct(struct_name, val)

        return val

    def instantiate_struct(self, name: str, value_dict: Dict[str, Any]) -> Any:
        """Instantiates a ctypes Structure from a dictionary."""
        if not self.structs_module:
             raise ImportError(f"Could not load structs module for {self.lib_name}")
             
        struct_class = getattr(self.structs_module, name)
        
        # We need to recursively instantiate fields
        processed_values = {}
        # We'd need type info for fields here, but usually values in test_plan 
        # for structs are primitive or should be already flattened.
        # For simplicity in v1.0, we assume field values are compatible.
        return struct_class(**value_dict)
