"""
ABI Extractor

Extracts ABI-specific details from libclang AST nodes including struct layouts
with explicit padding, calling conventions, and type information.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import clang.cindex as clang
except ImportError:
    raise ImportError("libclang not found. Install with: pip install libclang")


@dataclass
class PaddingField:
    """Represents implicit padding in a struct."""
    name: str
    offset_bytes: int
    size_bytes: int
    is_implicit: bool = True


class ABIExtractor:
    """
    Extracts ABI-specific information from AST nodes.
    
    Responsibilities:
    - Compute struct layouts with explicit padding
    - Extract type information (size, alignment)
    - Determine calling conventions
    - Handle recursive type representations
    """
    
    def __init__(self):
        """Initialize ABI extractor."""
        pass
    
    def compute_struct_layout(self, cursor) -> Dict[str, Any]:
        """
        Compute complete struct layout including explicit padding.
        
        Args:
            cursor: libclang cursor for struct declaration
            
        Returns:
            Dictionary with struct layout information including:
            - size_bytes: Total struct size
            - alignment_bytes: Struct alignment
            - fields: List of fields including padding
            - is_packed: Whether struct is packed
            - is_union: Whether this is a union
        """
        struct_type = cursor.type
        size_bytes = struct_type.get_size()
        alignment_bytes = struct_type.get_align()
        is_union = cursor.kind == clang.CursorKind.UNION_DECL
        
        # Extract declared fields
        declared_fields = []
        for field_cursor in cursor.get_children():
            if field_cursor.kind == clang.CursorKind.FIELD_DECL:
                field_info = self._extract_field_info(field_cursor)
                declared_fields.append(field_info)
        
        # Insert padding fields
        fields_with_padding = self.calculate_padding(
            declared_fields,
            size_bytes,
            alignment_bytes,
            is_union
        )
        
        return {
            "size_bytes": size_bytes,
            "alignment_bytes": alignment_bytes,
            "fields": fields_with_padding,
            "is_packed": self._is_packed(cursor),
            "is_union": is_union
        }
    
    def _extract_field_info(self, field_cursor) -> Dict[str, Any]:
        """
        Extract information about a single struct field.
        
        Args:
            field_cursor: libclang cursor for field declaration
            
        Returns:
            Dictionary with field information
        """
        field_name = field_cursor.spelling
        field_type = field_cursor.type
        
        # Get offset in bits, convert to bytes
        try:
            offset_bits = field_cursor.get_field_offsetof()
            offset_bytes = offset_bits // 8
        except:
            offset_bytes = 0
        
        type_info = self.extract_type_info(field_type)
        
        return {
            "name": field_name,
            "offset_bytes": offset_bytes,
            "type": type_info,
            "is_implicit": False
        }
    
    def calculate_padding(
        self,
        fields: List[Dict[str, Any]],
        total_size: int,
        alignment: int,
        is_union: bool
    ) -> List[Dict[str, Any]]:
        """
        Calculate and insert padding fields between declared fields.
        
        Args:
            fields: List of declared fields
            total_size: Total struct size in bytes
            alignment: Struct alignment in bytes
            is_union: Whether this is a union (no padding in unions)
            
        Returns:
            List of fields with padding fields inserted
        """
        if is_union or not fields:
            return fields
        
        result = []
        padding_counter = 1
        
        # Sort fields by offset
        sorted_fields = sorted(fields, key=lambda f: f["offset_bytes"])
        
        for i, field in enumerate(sorted_fields):
            # Add the field
            result.append(field)
            
            # Calculate expected next offset
            current_offset = field["offset_bytes"]
            current_size = field["type"]["size_bytes"]
            expected_next = current_offset + current_size
            
            # Check if there's a next field
            if i + 1 < len(sorted_fields):
                next_offset = sorted_fields[i + 1]["offset_bytes"]
                
                # If gap exists, insert padding
                if next_offset > expected_next:
                    padding_size = next_offset - expected_next
                    padding_field = {
                        "name": f"__padding_{padding_counter}",
                        "offset_bytes": expected_next,
                        "type": {
                            "kind": "padding",
                            "size_bytes": padding_size
                        },
                        "is_implicit": True
                    }
                    result.append(padding_field)
                    padding_counter += 1
        
        # Check for trailing padding
        if sorted_fields:
            last_field = sorted_fields[-1]
            last_end = last_field["offset_bytes"] + last_field["type"]["size_bytes"]
            
            if total_size > last_end:
                trailing_padding = total_size - last_end
                padding_field = {
                    "name": f"__padding_{padding_counter}",
                    "offset_bytes": last_end,
                    "type": {
                        "kind": "padding",
                        "size_bytes": trailing_padding
                    },
                    "is_implicit": True
                }
                result.append(padding_field)
        
        return result
    
    def extract_type_info(self, clang_type) -> Dict[str, Any]:
        """
        Extract complete type information recursively.
        
        Args:
            clang_type: libclang Type object
            
        Returns:
            Dictionary with type information including kind, size, alignment
        """
        type_kind = clang_type.kind
        
        # Primitive types
        if type_kind in [
            clang.TypeKind.VOID, clang.TypeKind.BOOL,
            clang.TypeKind.CHAR_U, clang.TypeKind.UCHAR, clang.TypeKind.CHAR16,
            clang.TypeKind.CHAR32, clang.TypeKind.USHORT, clang.TypeKind.UINT,
            clang.TypeKind.ULONG, clang.TypeKind.ULONGLONG, clang.TypeKind.UINT128,
            clang.TypeKind.CHAR_S, clang.TypeKind.SCHAR, clang.TypeKind.WCHAR,
            clang.TypeKind.SHORT, clang.TypeKind.INT, clang.TypeKind.LONG,
            clang.TypeKind.LONGLONG, clang.TypeKind.INT128, clang.TypeKind.FLOAT,
            clang.TypeKind.DOUBLE, clang.TypeKind.LONGDOUBLE
        ]:
            return {
                "kind": "primitive",
                "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Pointer types
        elif type_kind == clang.TypeKind.POINTER:
            pointee = clang_type.get_pointee()
            return {
                "kind": "pointer",
                "pointee": self.extract_type_info(pointee),
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Array types
        elif type_kind == clang.TypeKind.CONSTANTARRAY:
            element_type = clang_type.get_array_element_type()
            array_size = clang_type.get_array_size()
            return {
                "kind": "array",
                "element_type": self.extract_type_info(element_type),
                "size": array_size,
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Typedef types - record the typedef but also resolve it
        elif type_kind == clang.TypeKind.TYPEDEF:
            canonical = clang_type.get_canonical()
            return {
                "kind": "typedef",
                "name": clang_type.spelling,
                "underlying_type": self.extract_type_info(canonical),
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Record types (struct/union)
        elif type_kind == clang.TypeKind.RECORD:
            return {
                "kind": "record",
                "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Enum types
        elif type_kind == clang.TypeKind.ENUM:
            return {
                "kind": "enum",
                "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Function pointer types
        elif type_kind == clang.TypeKind.FUNCTIONPROTO:
            return {
                "kind": "function_pointer",
                "size_bytes": clang_type.get_size(),
                "alignment_bytes": clang_type.get_align()
            }
        
        # Fallback for unknown types
        else:
            return {
                "kind": "unknown",
                "name": clang_type.spelling,
                "size_bytes": clang_type.get_size() if clang_type.get_size() > 0 else 0,
                "alignment_bytes": clang_type.get_align() if clang_type.get_align() > 0 else 0
            }
    
    def determine_calling_convention(self, cursor) -> str:
        """
        Determine calling convention for a function.
        
        Args:
            cursor: libclang cursor for function declaration
            
        Returns:
            Calling convention name: "cdecl", "stdcall", "fastcall", etc.
        """
        try:
            func_type = cursor.type
            calling_conv = func_type.get_calling_conv()
            
            if calling_conv == clang.CallingConv.C:
                return "cdecl"
            elif calling_conv == clang.CallingConv.X86_STDCALL:
                return "stdcall"
            elif calling_conv == clang.CallingConv.X86_FASTCALL:
                return "fastcall"
            elif calling_conv == clang.CallingConv.X86_THISCALL:
                return "thiscall"
            elif calling_conv == clang.CallingConv.WIN64:
                return "win64"
            else:
                return "cdecl"  # Default
        except:
            return "cdecl"
    
    def _is_packed(self, cursor) -> bool:
        """
        Determine if struct is packed (no padding).
        
        Args:
            cursor: libclang cursor for struct
            
        Returns:
            True if packed, False otherwise
        """
        # Check for __attribute__((packed)) or #pragma pack
        # This is a simplified check - full implementation would parse attributes
        for child in cursor.get_children():
            if child.kind == clang.CursorKind.PACKED_ATTR:
                return True
        return False
