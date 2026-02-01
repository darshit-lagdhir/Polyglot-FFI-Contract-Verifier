"""
Native Interface Analyzer

Main orchestrator for native interface ingestion. Coordinates parsing, extraction,
and artifact generation to produce compiler-grade ABI information from C headers.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import clang.cindex as clang
except ImportError:
    raise ImportError("libclang not found. Install with: pip install libclang")

from .compiler_frontend import CompilerFrontend
from .abi_extractor import ABIExtractor
from .source_location_tracker import SourceLocationTracker


class NativeInterfaceAnalyzer:
    """
    Main analyzer for native interface ingestion.
    
    Responsibilities:
    - Orchestrate the ingestion process
    - Parse headers using CompilerFrontend
    - Extract functions, structs, enums, typedefs
    - Generate Native Interface Artifact
    - Ensure provenance tracking
    """
    
    def __init__(self):
        """Initialize analyzer with required components."""
        self.frontend = CompilerFrontend()
        self.abi_extractor = ABIExtractor()
        self.location_tracker = SourceLocationTracker()
    
    def analyze(
        self,
        header_path: str,
        library_path: str,
        context
    ) -> Dict[str, Any]:
        """
        Analyze a C header file and produce Native Interface Artifact.
        
        Args:
            header_path: Absolute path to C header file
            library_path: Absolute path to native library (for validation)
            context: ExecutionContext from Phase 1
            
        Returns:
            Native Interface Artifact as dictionary
            
        Raises:
            ToolingError: If parsing or extraction fails
        """
        # Parse header
        tu = self.frontend.parse_header(header_path, context)
        
        # Extract all symbols
        functions = self.extract_functions(tu.cursor)
        structs = self.extract_structs(tu.cursor)
        enums = self.extract_enums(tu.cursor)
        typedefs = self.extract_typedefs(tu.cursor)
        
        # Build artifact
        artifact = self._build_artifact(
            functions=functions,
            structs=structs,
            enums=enums,
            typedefs=typedefs,
            header_path=header_path,
            library_path=library_path,
            context=context
        )
        
        return artifact
    
    def extract_functions(self, cursor) -> List[Dict[str, Any]]:
        """
        Extract all function declarations from AST.
        
        Args:
            cursor: Root cursor of translation unit
            
        Returns:
            List of function declarations with full signatures
        """
        functions = []
        
        for node in cursor.walk_preorder():
            # Only process function declarations with external linkage
            if node.kind == clang.CursorKind.FUNCTION_DECL:
                if node.linkage == clang.LinkageKind.EXTERNAL:
                    func_info = self._extract_function_info(node)
                    functions.append(func_info)
        
        return functions
    
    def extract_structs(self, cursor) -> List[Dict[str, Any]]:
        """
        Extract all struct declarations from AST.
        
        Args:
            cursor: Root cursor of translation unit
            
        Returns:
            List of struct declarations with complete layouts
        """
        structs = []
        seen_names = set()
        
        for node in cursor.walk_preorder():
            if node.kind in [clang.CursorKind.STRUCT_DECL, clang.CursorKind.UNION_DECL]:
                # Only process complete definitions, not forward declarations
                if node.is_definition():
                    struct_name = node.spelling
                    
                    # Avoid duplicates
                    if struct_name and struct_name not in seen_names:
                        seen_names.add(struct_name)
                        struct_info = self._extract_struct_info(node)
                        structs.append(struct_info)
        
        return structs
    
    def extract_enums(self, cursor) -> List[Dict[str, Any]]:
        """
        Extract all enum declarations from AST.
        
        Args:
            cursor: Root cursor of translation unit
            
        Returns:
            List of enum declarations with values
        """
        enums = []
        seen_names = set()
        
        for node in cursor.walk_preorder():
            if node.kind == clang.CursorKind.ENUM_DECL:
                if node.is_definition():
                    enum_name = node.spelling
                    
                    # Avoid duplicates
                    if enum_name and enum_name not in seen_names:
                        seen_names.add(enum_name)
                        enum_info = self._extract_enum_info(node)
                        enums.append(enum_info)
        
        return enums
    
    def extract_typedefs(self, cursor) -> List[Dict[str, Any]]:
        """
        Extract all typedef declarations from AST.
        
        Args:
            cursor: Root cursor of translation unit
            
        Returns:
            List of typedef declarations
        """
        typedefs = []
        seen_names = set()
        
        for node in cursor.walk_preorder():
            if node.kind == clang.CursorKind.TYPEDEF_DECL:
                typedef_name = node.spelling
                
                # Avoid duplicates
                if typedef_name and typedef_name not in seen_names:
                    seen_names.add(typedef_name)
                    typedef_info = self._extract_typedef_info(node)
                    typedefs.append(typedef_info)
        
        return typedefs
    
    def _extract_function_info(self, cursor) -> Dict[str, Any]:
        """Extract complete information about a function."""
        func_name = cursor.spelling
        func_type = cursor.type
        
        # Extract return type
        return_type = self.abi_extractor.extract_type_info(func_type.get_result())
        
        # Extract parameters
        parameters = []
        for arg in cursor.get_arguments():
            param_info = {
                "name": arg.spelling if arg.spelling else f"param{len(parameters)}",
                "type": self.abi_extractor.extract_type_info(arg.type),
                "qualifiers": self._extract_qualifiers(arg.type)
            }
            parameters.append(param_info)
        
        # Determine if variadic
        is_variadic = func_type.is_function_variadic()
        
        # Get calling convention
        calling_convention = self.abi_extractor.determine_calling_convention(cursor)
        
        # Get source location
        source_location = self.location_tracker.get_location_dict(cursor)
        
        return {
            "name": func_name,
            "source_location": source_location,
            "linkage": "external",
            "calling_convention": calling_convention,
            "return_type": return_type,
            "parameters": parameters,
            "is_variadic": is_variadic,
            "attributes": []
        }
    
    def _extract_struct_info(self, cursor) -> Dict[str, Any]:
        """Extract complete information about a struct."""
        struct_name = cursor.spelling
        
        # Compute layout with padding
        layout = self.abi_extractor.compute_struct_layout(cursor)
        
        # Get source location
        source_location = self.location_tracker.get_location_dict(cursor)
        
        return {
            "name": struct_name,
            "source_location": source_location,
            "size_bytes": layout["size_bytes"],
            "alignment_bytes": layout["alignment_bytes"],
            "fields": layout["fields"],
            "is_packed": layout["is_packed"],
            "is_union": layout["is_union"]
        }
    
    def _extract_enum_info(self, cursor) -> Dict[str, Any]:
        """Extract complete information about an enum."""
        enum_name = cursor.spelling
        
        # Get underlying type
        enum_type = cursor.enum_type
        underlying_type = self.abi_extractor.extract_type_info(enum_type)
        
        # Extract enum values
        values = []
        for child in cursor.get_children():
            if child.kind == clang.CursorKind.ENUM_CONSTANT_DECL:
                values.append({
                    "name": child.spelling,
                    "value": child.enum_value
                })
        
        # Get source location
        source_location = self.location_tracker.get_location_dict(cursor)
        
        return {
            "name": enum_name,
            "source_location": source_location,
            "underlying_type": underlying_type,
            "values": values
        }
    
    def _extract_typedef_info(self, cursor) -> Dict[str, Any]:
        """Extract complete information about a typedef."""
        typedef_name = cursor.spelling
        
        # Get underlying type
        underlying_type = cursor.underlying_typedef_type
        type_info = self.abi_extractor.extract_type_info(underlying_type)
        
        # Get source location
        source_location = self.location_tracker.get_location_dict(cursor)
        
        return {
            "name": typedef_name,
            "source_location": source_location,
            "underlying_type": type_info
        }
    
    def _extract_qualifiers(self, clang_type) -> List[str]:
        """Extract type qualifiers (const, volatile, etc.)."""
        qualifiers = []
        
        if clang_type.is_const_qualified():
            qualifiers.append("const")
        if clang_type.is_volatile_qualified():
            qualifiers.append("volatile")
        if clang_type.is_restrict_qualified():
            qualifiers.append("restrict")
        
        return qualifiers
    
    def _build_artifact(
        self,
        functions: List[Dict[str, Any]],
        structs: List[Dict[str, Any]],
        enums: List[Dict[str, Any]],
        typedefs: List[Dict[str, Any]],
        header_path: str,
        library_path: str,
        context
    ) -> Dict[str, Any]:
        """Build complete Native Interface Artifact."""
        # Get compiler invocation for provenance
        compiler_invocation = self.frontend.get_compiler_invocation_string(
            header_path,
            context
        )
        
        # Build artifact
        artifact = {
            "provenance": {
                "producing_phase": "Native Interface Ingestion",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [
                    os.path.abspath(header_path),
                    os.path.abspath(library_path)
                ],
                "compiler_invocation": compiler_invocation
            },
            "platform": {
                "os_name": context.platform.os_name,
                "architecture": context.platform.architecture,
                "pointer_width": context.platform.pointer_width,
                "endianness": context.platform.endianness
            },
            "functions": functions,
            "structs": structs,
            "enums": enums,
            "typedefs": typedefs
        }
        
        return artifact
    
    def save_artifact(self, artifact: Dict[str, Any], output_path: str):
        """
        Save Native Interface Artifact to JSON file.
        
        Args:
            artifact: Native Interface Artifact dictionary
            output_path: Path to save artifact
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write artifact
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)
