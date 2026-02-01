"""
Input Value Generator
Produces deterministic concrete values for test cases.
"""

from typing import Dict, Any, List, Optional

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
