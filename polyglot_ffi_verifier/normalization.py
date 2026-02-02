"""
Normalization Module

This module handles the transformation of raw Native Interface Artifacts into 
canonical Intermediate Representation (IR).

Consolidates:
- IRNormalizer: Main orchestrator
- TypeResolver: Resolves typedefs and generates deterministic type IDs
- LayoutNormalizer: Normalizes struct/union layouts
- QualifierNormalizer: Normalizes type qualifiers

From original implementation:  (src/representation/)
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class QualifierNormalizer:
    """
    Normalizes type qualifiers from compiler-specific lists to canonical boolean maps.
    """
    
    def normalize(self, qualifiers: List[str]) -> Dict[str, bool]:
        """
        Convert a list of qualifier strings into a normalized dictionary.
        
        Args:
            qualifiers: List of strings like ["const", "volatile"]
            
        Returns:
            Dictionary with canonical keys and boolean values
        """
        # Ensure input is a list
        if not isinstance(qualifiers, list):
            qualifiers = []
            
        # Case insensitive matching
        q_lower = [q.lower() for q in qualifiers]
        
        return {
            "is_const": "const" in q_lower,
            "is_volatile": "volatile" in q_lower,
            "is_restrict": "restrict" in q_lower
        }

    @staticmethod
    def extract_from_type(type_info: Dict) -> Dict[str, bool]:
        """ Helper to extract qualifiers from a type info dictionary if present. """
        qualifiers = type_info.get("qualifiers", [])
        return QualifierNormalizer().normalize(qualifiers)

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
                # Fallback for void* or incomplete pointers if pointee missing
                # But mostly this should raise error or handle void*
                # Assuming generic void* if missing or check if it's handled upstream
                # For safety, let's raise if critical, but if it happens in void* case:
                # In our extractor, pointer always has pointee.
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
            # Try to get count from type info if not in top level, 
            # In ABIExtractor array size is "size".
            if count == 0 and "size" in type_info:
                 count = type_info["size"]
                 
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

class LayoutNormalizer:
    """
    Handles structural normalization of layouts (structs, unions).
    """
    
    def __init__(self, type_resolver: TypeResolver):
        self.type_resolver = type_resolver
        
    def normalize_struct(self, struct_info: Dict[str, Any], type_registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a struct definition.
        """
        type_id = self.type_resolver.resolve_type(struct_info, type_registry)
        
        normalized_fields = []
        for field in struct_info.get("fields", []):
            field_type = field.get("type")
            if not field_type:
                continue
                
            field_type_id = self.type_resolver.resolve_type(field_type, type_registry)
            
            normalized_field = {
                "name": field.get("name"),
                "offset_bytes": field.get("offset_bytes"),
                "type_id": field_type_id
            }
            
            # Preserve bit width if present
            if field.get("bit_width") is not None:
                normalized_field["bit_width"] = field["bit_width"]
                
            # Preserve implicit flag (for padding)
            if field.get("is_implicit"):
                normalized_field["is_implicit"] = True
                
            normalized_fields.append(normalized_field)
            
        return {
            "name": struct_info.get("name"),
            "type_id": type_id,
            "source_location": struct_info.get("source_location"),
            "size_bytes": struct_info.get("size_bytes"),
            "alignment_bytes": struct_info.get("alignment_bytes"),
            "fields": normalized_fields,
            "is_packed": struct_info.get("is_packed", False),
            "is_union": struct_info.get("is_union", False)
        }

# ============================================================================
# PUBLIC API
# ============================================================================

class IRNormalizer:
    """
    Orchestrates the IR normalization process.
    Produces Intermediate Representation from Native Interface Artifact.
    """
    
    def __init__(self):
        self.qualifier_normalizer = QualifierNormalizer()
        
    def normalize(self, context) -> Dict[str, Any]:
        """
        Produce Intermediate Representation from Native Interface Artifact.
        
        Args:
            context: ExecutionContext containing path to native interface artifact
        
        Returns:
            IR Artifact dictionary
        """
        # 1. Load native interface
        # The path should be from context
        native_interface_path = context.artifacts.native_interface_path
        
        if not os.path.exists(native_interface_path):
            raise FileNotFoundError(f"Native Interface Artifact not found at {native_interface_path}. Run Ingestion first.")
            
        with open(native_interface_path, 'r', encoding='utf-8') as f:
            ni = json.load(f)
            
        # 2. Initialize sub-components
        type_resolver = TypeResolver(ni.get("platform", {}))
        layout_normalizer = LayoutNormalizer(type_resolver)
        
        type_registry = {}
        
        # 3. Normalize Enums first (simplest types)
        normalized_enums = []
        for enum in ni.get("enums", []):
            normalized_enums.append(self._normalize_enum(enum, type_resolver, type_registry))
            
        # 4. Normalize Structs
        normalized_structs = []
        for struct in ni.get("structs", []):
            normalized_structs.append(layout_normalizer.normalize_struct(struct, type_registry))
            
        # 5. Normalize Functions
        normalized_functions = []
        for func in ni.get("functions", []):
            normalized_functions.append(self._normalize_function(func, type_resolver, type_registry))
            
        # 6. Build IR Artifact
        ir_artifact = {
            "provenance": {
                "producing_phase": ": Intermediate Representation Normalization",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(native_interface_path)]
            },
            "platform": ni.get("platform"),
            "type_registry": type_registry,
            "functions": normalized_functions,
            "structs": normalized_structs,
            "enums": normalized_enums
        }
        
        return ir_artifact

    def _normalize_enum(self, enum: Dict, resolver: TypeResolver, registry: Dict) -> Dict:
        type_id = resolver.resolve_type(enum, registry)
        underlying_type = enum.get("underlying_type", {"kind": "primitive", "name": "int"})
        underlying_id = resolver.resolve_type(underlying_type, registry)
        
        return {
            "name": enum.get("name"),
            "type_id": type_id,
            "source_location": enum.get("source_location"),
            "underlying_type_id": underlying_id,
            "values": enum.get("values", [])
        }

    def _normalize_function(self, func: Dict, resolver: TypeResolver, registry: Dict) -> Dict:
        return_type_id = resolver.resolve_type(func.get("return_type", {}), registry)
        
        normalized_params = []
        for param in func.get("parameters", []):
            p_type = param.get("type", {})
            p_type_id = resolver.resolve_type(p_type, registry)
            
            normalized_params.append({
                "name": param.get("name"),
                "type_id": p_type_id,
                "qualifiers": self.qualifier_normalizer.normalize(param.get("qualifiers", []))
            })
            
        return {
            "name": func.get("name"),
            "mangled_name": func.get("mangled_name"),
            "source_location": func.get("source_location"),
            "linkage": func.get("linkage", "external"),
            "calling_convention": func.get("calling_convention", "cdecl"),
            "return_type_id": return_type_id,
            "parameters": normalized_params,
            "is_variadic": func.get("is_variadic", False),
            "attributes": func.get("attributes", [])
        }

    def save_artifact(self, artifact: Dict[str, Any], output_path: str):
        """
        Save IR Artifact to JSON file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)
