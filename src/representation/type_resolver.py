"""
Type Resolver
Resolves typedef chains and produces canonical, compiler-agnostic type IDs.
"""

from typing import Dict, List, Any, Optional

class TypeResolver:
    """
    Handles type normalization, typedef resolution, and deterministic ID generation.
    """
    
    def __init__(self, platform_info: Dict[str, Any]):
        """
        Initialize with platform information for correct primitive mapping.
        """
        self.os_name = platform_info.get("os_name", "Windows")
        self.arch = platform_info.get("architecture", "AMD64")
        self.ptr_width = platform_info.get("pointer_width", 64)
        
        # Primitive mapping table for Windows x64
        self._primitive_map = {
            "void": "void",
            "bool": "bool",
            "_Bool": "bool",
            "char": "int8",  # Standard MSVC char is signed by default
            "signed char": "int8",
            "unsigned char": "uint8",
            "short": "int16",
            "signed short": "int16",
            "unsigned short": "uint16",
            "int": "int32",
            "signed int": "int32",
            "unsigned int": "uint32",
            "long": "int32",  # Windows x64 specific: long is 32-bit (LLP64)
            "signed long": "int32",
            "unsigned long": "uint32",
            "long long": "int64",
            "signed long long": "int64",
            "unsigned long long": "uint64",
            "__int64": "int64",
            "float": "float32",
            "double": "float64",
            "long double": "float64", # MSVC treats long double as double
            "size_t": "uint64" if self.ptr_width == 64 else "uint32",
            "wchar_t": "wchar"
        }

    def resolve_type(self, type_info: Dict[str, Any], type_registry: Dict[str, Any]) -> str:
        """
        Resolve a type to its canonical ID and ensure it exists in the registry.
        
        Returns:
            The type_id (e.g., "primitive:int32")
        """
        kind = type_info.get("kind")
        
        # 1. Resolve Typedefs transitively
        if kind == "typedef":
            underlying = type_info.get("underlying_type")
            if not underlying:
                raise ValueError(f"Malformed typedef: {type_info.get('name')}")
            return self.resolve_type(underlying, type_registry)
            
        # 2. Handle Primitives
        if kind == "primitive":
            raw_name = type_info.get("name", "unknown")
            canon_name = self._primitive_map.get(raw_name, raw_name)
            type_id = f"primitive:{canon_name}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "primitive",
                    "canonical_name": canon_name,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes")
                }
            return type_id
            
        # 3. Handle Pointers
        if kind == "pointer":
            pointee = type_info.get("pointee")
            if not pointee:
                raise ValueError("Malformed pointer: missing pointee")
                
            pointee_id = self.resolve_type(pointee, type_registry)
            type_id = f"pointer:{pointee_id}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "pointer",
                    "canonical_name": f"pointer<{pointee_id}>",
                    "pointee_type_id": pointee_id,
                    "size_bytes": type_info.get("size_bytes", self.ptr_width // 8),
                    "alignment_bytes": type_info.get("alignment_bytes", self.ptr_width // 8)
                }
            return type_id
            
        # 4. Handle Structs
        if kind in ["struct", "record"]:
            name = type_info.get("name", "anonymous_struct")
            type_id = f"struct:{name}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "struct",
                    "canonical_name": name,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes"),
                    "source_location": type_info.get("source_location")
                }
            return type_id

        # 5. Handle Enums
        if kind == "enum":
            name = type_info.get("name", "anonymous_enum")
            type_id = f"enum:{name}"
            
            if type_id not in type_registry:
                underlying = type_info.get("underlying_type", {"kind": "primitive", "name": "int"})
                underlying_id = self.resolve_type(underlying, type_registry)
                
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "enum",
                    "canonical_name": name,
                    "underlying_type_id": underlying_id,
                    "size_bytes": type_info.get("size_bytes", 4),
                    "alignment_bytes": type_info.get("alignment_bytes", 4),
                    "source_location": type_info.get("source_location")
                }
            return type_id
            
        # 6. Handle Padding
        if kind == "padding":
            size = type_info.get("size_bytes", 0)
            type_id = f"padding:{size}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "padding",
                    "size_bytes": size
                }
            return type_id

        # 7. Handle Arrays
        if kind == "array":
            element = type_info.get("element_type")
            count = type_info.get("element_count", 0)
            element_id = self.resolve_type(element, type_registry)
            type_id = f"array:{element_id}:{count}"
            
            if type_id not in type_registry:
                type_registry[type_id] = {
                    "id": type_id,
                    "kind": "array",
                    "element_type_id": element_id,
                    "element_count": count,
                    "size_bytes": type_info.get("size_bytes"),
                    "alignment_bytes": type_info.get("alignment_bytes")
                }
            return type_id

        return f"unknown:{type_info.get('name', 'unnamed')}"
