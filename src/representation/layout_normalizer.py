"""
Layout Normalizer
Normalizes struct layouts by replacing inline types with type ID references.
"""

from typing import Dict, List, Any
from .type_resolver import TypeResolver

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
