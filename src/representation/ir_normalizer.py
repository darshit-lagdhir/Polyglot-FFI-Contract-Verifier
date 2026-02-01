"""
IR Normalizer
Main orchestrator for transforming Native Interface Artifact into canonical IR.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

from .type_resolver import TypeResolver
from .qualifier_normalizer import QualifierNormalizer
from .layout_normalizer import LayoutNormalizer

class IRNormalizer:
    """
    Orchestrates the IR normalization process.
    """
    
    def __init__(self):
        self.qualifier_normalizer = QualifierNormalizer()
        
    def normalize(self, context) -> Dict[str, Any]:
        """
        Produce Intermediate Representation from Native Interface Artifact.
        """
        # 1. Load native interface
        # In actual run, it would be in artifacts directory
        # The path should be from context if available, or default
        # But Phase 2 might not have recorded the path in context yet, 
        # so we look at the default location if needed.
        # Actually, our orchestration update should ensure it's there.
        
        native_interface_path = getattr(context.artifacts, 'native_interface_path', 
                                     os.path.join(context.artifacts.working_directory, "artifacts", "native_interface.json"))
        
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
                "producing_phase": "Phase 3: Intermediate Representation Normalization",
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
