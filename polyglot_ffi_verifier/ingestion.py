"""
Ingestion Module

This module orchestrates native interface ingestion. It coordinates parsing, extraction,
and artifact generation to produce compiler-grade ABI information from C headers.

Consolidates:
- NativeInterfaceAnalyzer: Main orchestrator
- CompilerFrontend: Interfaces with libclang
- ABIExtractor: Extracts ABI-specific details
- SourceLocationTracker: Formats source locations

From original implementation: Phase 2 (src/ingestion/)
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from dataclasses import dataclass

# ============================================================================
# EXTERNAL DEPENDENCIES (libclang)
# ============================================================================

def _configure_libclang():
    """Configure libclang library path for Windows."""
    common_paths = [
        r"C:\Program Files\LLVM\bin\libclang.dll",
        r"C:\Program Files (x86)\LLVM\bin\libclang.dll",
        r"C:\LLVM\bin\libclang.dll",
    ]
    env_path = os.environ.get('LIBCLANG_PATH')
    if env_path and os.path.exists(env_path):
        import clang.cindex
        clang.cindex.Config.set_library_file(env_path)
        return
    for path in common_paths:
        if os.path.exists(path):
            import clang.cindex
            clang.cindex.Config.set_library_file(path)
            return

_configure_libclang()
try:
    import clang.cindex as clang
except ImportError:
    # We allow import error here, but classes will fail if instantiated
    clang = None

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

@dataclass(frozen=True)
class SourceLocation:
    """Immutable source location representation."""
    file: str
    line: int
    column: int

class SourceLocationTracker:
    """Tracks and formats source locations from AST nodes."""
    
    def get_location(self, cursor) -> SourceLocation:
        try:
            location = cursor.location
            if location.file:
                file_path = os.path.abspath(location.file.name)
                return SourceLocation(file=file_path, line=location.line, column=location.column)
            else:
                return self._unknown_location()
        except Exception:
            return self._unknown_location()
    
    def format_location(self, location: SourceLocation) -> Dict[str, Any]:
        return {"file": location.file, "line": location.line, "column": location.column}
    
    def _unknown_location(self) -> SourceLocation:
        return SourceLocation(file="<unknown>", line=0, column=0)
    
    def get_location_dict(self, cursor) -> Dict[str, Any]:
        location = self.get_location(cursor)
        return self.format_location(location)


class ABIExtractor:
    """Extracts ABI-specific information from AST nodes."""
    
    def compute_struct_layout(self, cursor) -> Dict[str, Any]:
        struct_type = cursor.type
        size_bytes = struct_type.get_size()
        alignment_bytes = struct_type.get_align()
        is_union = cursor.kind == clang.CursorKind.UNION_DECL
        
        declared_fields = []
        for field_cursor in cursor.get_children():
            if field_cursor.kind == clang.CursorKind.FIELD_DECL:
                field_info = self._extract_field_info(field_cursor)
                declared_fields.append(field_info)
        
        fields_with_padding = self.calculate_padding(declared_fields, size_bytes, alignment_bytes, is_union)
        
        return {
            "size_bytes": size_bytes,
            "alignment_bytes": alignment_bytes,
            "fields": fields_with_padding,
            "is_packed": self._is_packed(cursor),
            "is_union": is_union
        }
    
    def _extract_field_info(self, field_cursor) -> Dict[str, Any]:
        field_name = field_cursor.spelling
        field_type = field_cursor.type
        try:
            offset_bits = field_cursor.get_field_offsetof()
            offset_bytes = offset_bits // 8
        except:
            offset_bytes = 0
        
        type_info = self.extract_type_info(field_type)
        return {"name": field_name, "offset_bytes": offset_bytes, "type": type_info, "is_implicit": False}
    
    def calculate_padding(self, fields: List[Dict[str, Any]], total_size: int, alignment: int, is_union: bool) -> List[Dict[str, Any]]:
        if is_union or not fields: return fields
        result = []
        padding_counter = 1
        sorted_fields = sorted(fields, key=lambda f: f["offset_bytes"])
        
        for i, field in enumerate(sorted_fields):
            result.append(field)
            current_offset = field["offset_bytes"]
            current_size = field["type"]["size_bytes"]
            expected_next = current_offset + current_size
            
            if i + 1 < len(sorted_fields):
                next_offset = sorted_fields[i + 1]["offset_bytes"]
                if next_offset > expected_next:
                    padding_size = next_offset - expected_next
                    result.append({
                        "name": f"__padding_{padding_counter}",
                        "offset_bytes": expected_next,
                        "type": {"kind": "padding", "size_bytes": padding_size},
                        "is_implicit": True
                    })
                    padding_counter += 1

        if sorted_fields:
            last_field = sorted_fields[-1]
            last_end = last_field["offset_bytes"] + last_field["type"]["size_bytes"]
            if total_size > last_end:
                result.append({
                    "name": f"__padding_{padding_counter}",
                    "offset_bytes": last_end,
                    "type": {"kind": "padding", "size_bytes": total_size - last_end},
                    "is_implicit": True
                })
        return result
    
    def extract_type_info(self, clang_type) -> Dict[str, Any]:
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
                "kind": "primitive", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.POINTER:
             return {
                "kind": "pointer", "pointee": self.extract_type_info(clang_type.get_pointee()),
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.CONSTANTARRAY:
             return {
                "kind": "array", "element_type": self.extract_type_info(clang_type.get_array_element_type()),
                "size": clang_type.get_array_size(), "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.TYPEDEF:
             return {
                "kind": "typedef", "name": clang_type.spelling,
                "underlying_type": self.extract_type_info(clang_type.get_canonical()),
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.RECORD:
             return {
                "kind": "record", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.ENUM:
             return {
                "kind": "enum", "name": clang_type.spelling,
                "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()
            }
        elif type_kind == clang.TypeKind.FUNCTIONPROTO:
             return {"kind": "function_pointer", "size_bytes": clang_type.get_size(), "alignment_bytes": clang_type.get_align()}
        else:
             return {
                "kind": "unknown", "name": clang_type.spelling,
                "size_bytes": max(0, clang_type.get_size()), "alignment_bytes": max(0, clang_type.get_align())
            }

    def determine_calling_convention(self, cursor) -> str:
        try:
            conv = cursor.type.get_calling_conv()
            if conv == clang.CallingConv.C: return "cdecl"
            elif conv == clang.CallingConv.X86_STDCALL: return "stdcall"
            elif conv == clang.CallingConv.X86_FASTCALL: return "fastcall"
            elif conv == clang.CallingConv.X86_THISCALL: return "thiscall"
            elif conv == clang.CallingConv.WIN64: return "win64"
            else: return "cdecl"
        except:
            return "cdecl"

    def _is_packed(self, cursor) -> bool:
        for child in cursor.get_children():
            if child.kind == clang.CursorKind.PACKED_ATTR:
                return True
        return False


class CompilerFrontend:
    """Interfaces with libclang to parse C header files and provide AST access."""
    
    def __init__(self):
        if not clang:
            raise ImportError("libclang not found. Install with: pip install libclang")
        self.index = clang.Index.create()
    
    def parse_header(self, header_path: str, context):
        if not os.path.exists(header_path):
            raise Exception(f"Header file not found: {header_path}")
        
        args = self.get_compiler_command(context)
        try:
            tu = self.index.parse(
                header_path,
                args=args,
                options=(clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | clang.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
            )
        except Exception as e:
            raise Exception(f"Failed to parse header: {e}")
        
        if not self.validate_compilation(tu):
            raise Exception(f"Header compilation failed:\n{self._format_diagnostics(tu)}")
        return tu

    def get_compiler_command(self, context) -> List[str]:
        args = []
        for p in context.compiler.include_paths: args.append(f"-I{p}")
        for m in context.compiler.preprocessor_macros: args.append(f"-D{m}")
        if context.platform.os_name == "Windows":
             args.extend(["-fms-compatibility", "-fms-extensions", f"-fms-compatibility-version={context.compiler.compiler_version}"])
        if context.platform.architecture == "AMD64": args.append("-m64")
        return args

    def validate_compilation(self, tu) -> bool:
        for diag in tu.diagnostics:
            if diag.severity >= clang.Diagnostic.Error: return False
        return True

    def _format_diagnostics(self, tu) -> str:
        messages = []
        for diag in tu.diagnostics:
            loc = f"{diag.location.file.name}:{diag.location.line}:{diag.location.column}" if diag.location.file else "<unknown>"
            messages.append(f"Severity({diag.severity}): {loc}: {diag.spelling}")
        return "\n".join(messages) if messages else "No diagnostics available"
        
    def get_compiler_invocation_string(self, header_path: str, context) -> str:
        args = self.get_compiler_command(context)
        return f"clang {' '.join(args)} {header_path}"


class NativeInterfaceAnalyzer:
    """Main orchestrator for native interface ingestion."""

    def __init__(self):
        self.frontend = CompilerFrontend()
        self.abi_extractor = ABIExtractor()
        self.location_tracker = SourceLocationTracker()

    def analyze(self, header_path: str, library_path: str, context) -> Dict[str, Any]:
        tu = self.frontend.parse_header(header_path, context)
        
        functions = self.extract_functions(tu.cursor)
        structs = self.extract_structs(tu.cursor)
        enums = self.extract_enums(tu.cursor)
        typedefs = self.extract_typedefs(tu.cursor)
        
        return self._build_artifact(
            functions=functions, structs=structs, enums=enums, typedefs=typedefs,
            header_path=header_path, library_path=library_path, context=context
        )

    def extract_functions(self, cursor) -> List[Dict[str, Any]]:
        functions = []
        for node in cursor.walk_preorder():
            if node.kind == clang.CursorKind.FUNCTION_DECL and node.linkage == clang.LinkageKind.EXTERNAL:
                functions.append(self._extract_function_info(node))
        return functions

    def extract_structs(self, cursor) -> List[Dict[str, Any]]:
        structs = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind in [clang.CursorKind.STRUCT_DECL, clang.CursorKind.UNION_DECL] and node.is_definition():
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    structs.append(self._extract_struct_info(node))
        return structs

    def extract_enums(self, cursor) -> List[Dict[str, Any]]:
        enums = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind == clang.CursorKind.ENUM_DECL and node.is_definition():
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    enums.append(self._extract_enum_info(node))
        return enums

    def extract_typedefs(self, cursor) -> List[Dict[str, Any]]:
        typedefs = []
        seen = set()
        for node in cursor.walk_preorder():
            if node.kind == clang.CursorKind.TYPEDEF_DECL:
                if node.spelling and node.spelling not in seen:
                    seen.add(node.spelling)
                    typedefs.append(self._extract_typedef_info(node))
        return typedefs

    def _extract_function_info(self, cursor) -> Dict[str, Any]:
        func_name = cursor.spelling
        return_type = self.abi_extractor.extract_type_info(cursor.type.get_result())
        parameters = []
        for arg in cursor.get_arguments():
            parameters.append({
                "name": arg.spelling or f"param{len(parameters)}",
                "type": self.abi_extractor.extract_type_info(arg.type),
                "qualifiers": self._extract_qualifiers(arg.type)
            })
        
        return {
            "name": func_name,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "linkage": "external",
            "calling_convention": self.abi_extractor.determine_calling_convention(cursor),
            "return_type": return_type,
            "parameters": parameters,
            "is_variadic": cursor.type.is_function_variadic(),
            "attributes": []
        }

    def _extract_struct_info(self, cursor) -> Dict[str, Any]:
        layout = self.abi_extractor.compute_struct_layout(cursor)
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "size_bytes": layout["size_bytes"],
            "alignment_bytes": layout["alignment_bytes"],
            "fields": layout["fields"],
            "is_packed": layout["is_packed"],
            "is_union": layout["is_union"]
        }

    def _extract_enum_info(self, cursor) -> Dict[str, Any]:
        underlying = self.abi_extractor.extract_type_info(cursor.enum_type)
        values = []
        for child in cursor.get_children():
            if child.kind == clang.CursorKind.ENUM_CONSTANT_DECL:
                values.append({"name": child.spelling, "value": child.enum_value})
        
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "underlying_type": underlying,
            "values": values
        }

    def _extract_typedef_info(self, cursor) -> Dict[str, Any]:
        return {
            "name": cursor.spelling,
            "source_location": self.location_tracker.get_location_dict(cursor),
            "underlying_type": self.abi_extractor.extract_type_info(cursor.underlying_typedef_type)
        }

    def _extract_qualifiers(self, clang_type) -> List[str]:
        q = []
        if clang_type.is_const_qualified(): q.append("const")
        if clang_type.is_volatile_qualified(): q.append("volatile")
        if clang_type.is_restrict_qualified(): q.append("restrict")
        return q

    def _build_artifact(self, functions, structs, enums, typedefs, header_path, library_path, context) -> Dict[str, Any]:
        ci = self.frontend.get_compiler_invocation_string(header_path, context)
        return {
            "provenance": {
                "producing_phase": "Native Interface Ingestion",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(header_path), os.path.abspath(library_path)],
                "compiler_invocation": ci
            },
            "platform": {
                "os_name": context.platform.os_name,
                "architecture": context.platform.architecture,
                "pointer_width": context.platform.pointer_width,
                "endianness": context.platform.endianness
            },
            "functions": functions, "structs": structs, "enums": enums, "typedefs": typedefs
        }

    def save_artifact(self, artifact: Dict[str, Any], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)
