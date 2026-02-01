# Native Interface Ingestion Implementation

## Overview

This document describes the implementation of the **Native Interface Ingestion** component for the Polyglot FFI Contract Verifier. This component extracts compiler-grade ABI (Application Binary Interface) information from C header files using libclang.

### Position in Pipeline

```
ExecutionContext (Orchestration Layer)
  ↓
Native Interface Ingestion ← YOU ARE HERE
  ↓
IR Normalization (Phase 3)
  ↓
Contract Synthesis (Phase 4)
  ↓
... remaining phases
```

### Input Artifacts
- **ExecutionContext** - Immutable context from orchestration layer
- **C Header File(s)** - User-specified interface definitions
- **Native Library** - Binary for validation

### Output Artifacts
- **native_interface.json** - Complete ABI description with:
  - Functions with full signatures
  - Structs with explicit padding
  - Enums with values
  - Typedefs with underlying types
  - Complete provenance metadata

---

## Components Implemented

### 1. NativeInterfaceAnalyzer
**Location**: `src/ingestion/native_interface_analyzer.py`

Main orchestrator for the ingestion process.

**Responsibilities**:
- Coordinate parsing and extraction
- Walk AST to extract symbols
- Generate Native Interface Artifact
- Ensure provenance tracking

**Key Methods**:
```python
analyze(header_path, library_path, context) -> Dict
extract_functions(cursor) -> List[Dict]
extract_structs(cursor) -> List[Dict]
extract_enums(cursor) -> List[Dict]
extract_typedefs(cursor) -> List[Dict]
save_artifact(artifact, output_path)
```

### 2. CompilerFrontend
**Location**: `src/ingestion/compiler_frontend.py`

Interfaces with libclang for header parsing.

**Responsibilities**:
- Configure libclang with correct flags
- Parse headers into AST
- Validate compilation
- Report errors clearly

**Key Methods**:
```python
parse_header(header_path, context) -> TranslationUnit
get_compiler_command(context) -> List[str]
validate_compilation(tu) -> bool
```

**Windows/MSVC Integration**:
- Auto-detects libclang.dll from common LLVM paths
- Adds MSVC compatibility flags (`-fms-compatibility`)
- Uses include paths and macros from ExecutionContext
- Handles Windows SDK headers correctly

### 3. ABIExtractor
**Location**: `src/ingestion/abi_extractor.py`

Extracts ABI-specific details from AST nodes.

**Responsibilities**:
- Compute struct layouts with padding
- Extract type information recursively
- Determine calling conventions
- Calculate padding fields

**Key Methods**:
```python
compute_struct_layout(cursor) -> Dict
extract_type_info(clang_type) -> Dict
determine_calling_convention(cursor) -> str
calculate_padding(fields, total_size, alignment, is_union) -> List[Dict]
```

### 4. SourceLocationTracker
**Location**: `src/ingestion/source_location_tracker.py`

Captures source locations from AST nodes.

**Responsibilities**:
- Extract source locations from cursors
- Resolve to absolute paths
- Format consistently for artifacts
- Handle missing locations gracefully

**Key Methods**:
```python
get_location(cursor) -> SourceLocation
format_location(location) -> Dict
get_location_dict(cursor) -> Dict
```

---

## libclang Integration

### Installation
```bash
pip install libclang
```

### Configuration
The compiler frontend automatically configures libclang by searching common Windows paths:
- `C:\Program Files\LLVM\bin\libclang.dll`
- `C:\Program Files (x86)\LLVM\bin\libclang.dll`
- `C:\LLVM\bin\libclang.dll`

Alternatively, set the `LIBCLANG_PATH` environment variable.

### Usage Pattern
```python
import clang.cindex as clang

# Create index
index = clang.Index.create()

# Parse translation unit
tu = index.parse(
    header_path,
    args=['-I/include/path', '-DMACRO=value'],
    options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
)

# Walk AST
for cursor in tu.cursor.walk_preorder():
    if cursor.kind == clang.CursorKind.FUNCTION_DECL:
        # Extract function information
        pass
```

### Cursor Kinds Extracted
- `FUNCTION_DECL` - Function declarations
- `STRUCT_DECL` - Struct definitions
- `UNION_DECL` - Union definitions
- `ENUM_DECL` - Enum definitions
- `TYPEDEF_DECL` - Typedef declarations
- `FIELD_DECL` - Struct fields
- `ENUM_CONSTANT_DECL` - Enum values

---

## Struct Layout Computation

Struct layout is the most complex aspect of ingestion. The algorithm:

### Step 1: Extract Field Declarations
Iterate through struct fields in declaration order and extract name and type for each.

### Step 2: Compute Field Offsets
Use `cursor.get_field_offsetof()` from libclang:
- Returns offset in **bits**
- Divide by 8 to get bytes
- Offsets account for alignment and padding

### Step 3: Detect Implicit Padding
Compare consecutive field offsets:
```python
if offset[i+1] != offset[i] + size[i]:
    # Padding exists
    padding_size = offset[i+1] - (offset[i] + size[i])
    # Insert synthetic padding field
```

### Step 4: Compute Total Size and Alignment
- Total size: `cursor.type.get_size()`
- Alignment: `cursor.type.get_align()`
- Check for trailing padding

### Example

```c
struct Example {
    int a;      // offset 0, size 4
    // implicit padding: offset 4, size 4
    void* b;    // offset 8, size 8
    char c;     // offset 16, size 1
    // implicit trailing padding: offset 17, size 7
};
// Total size: 24, alignment: 8
```

**Artifact Representation**:
```json
{
  "name": "Example",
  "size_bytes": 24,
  "alignment_bytes": 8,
  "fields": [
    {
      "name": "a",
      "offset_bytes": 0,
      "type": {"kind": "primitive", "name": "int", "size_bytes": 4},
      "is_implicit": false
    },
    {
      "name": "__padding_1",
      "offset_bytes": 4,
      "type": {"kind": "padding", "size_bytes": 4},
      "is_implicit": true
    },
    {
      "name": "b",
      "offset_bytes": 8,
      "type": {"kind": "pointer", "size_bytes": 8},
      "is_implicit": false
    },
    {
      "name": "c",
      "offset_bytes": 16,
      "type": {"kind": "primitive", "name": "char", "size_bytes": 1},
      "is_implicit": false
    },
    {
      "name": "__padding_2",
      "offset_bytes": 17,
      "type": {"kind": "padding", "size_bytes": 7},
      "is_implicit": true
    }
  ]
}
```

---

## Type Representation

Types are represented recursively in the artifact.

### Primitive Types
```json
{
  "kind": "primitive",
  "name": "int",
  "size_bytes": 4,
  "alignment_bytes": 4
}
```

### Pointer Types
```json
{
  "kind": "pointer",
  "pointee": {
    "kind": "primitive",
    "name": "char",
    "size_bytes": 1
  },
  "size_bytes": 8,
  "alignment_bytes": 8
}
```

### Array Types
```json
{
  "kind": "array",
  "element_type": {"kind": "primitive", "name": "int"},
  "size": 10,
  "size_bytes": 40
}
```

### Typedef Types
```json
{
  "kind": "typedef",
  "name": "size_t",
  "underlying_type": {
    "kind": "primitive",
    "name": "unsigned long long",
    "size_bytes": 8
  }
}
```

---

## Calling Convention Detection

On Windows with MSVC, functions may use different calling conventions.

### Supported Conventions
- **cdecl** - Standard C calling convention (default)
- **stdcall** - Windows API convention (callee cleans stack)
- **fastcall** - First two args in registers
- **win64** - x64 Windows calling convention

### Detection Method
```python
calling_conv = cursor.type.get_calling_conv()
if calling_conv == clang.CallingConv.C:
    return "cdecl"
elif calling_conv == clang.CallingConv.X86_STDCALL:
    return "stdcall"
elif calling_conv == clang.CallingConv.X86_FASTCALL:
    return "fastcall"
elif calling_conv == clang.CallingConv.WIN64:
    return "win64"
```

### Example
```c
int __cdecl normal_func(int x);
int __stdcall windows_func(int x);
```

Artifact:
```json
{
  "name": "normal_func",
  "calling_convention": "cdecl",
  ...
},
{
  "name": "windows_func",
  "calling_convention": "stdcall",
  ...
}
```

---

## Error Handling

### Compilation Errors
If a header cannot be parsed:
- Report which header file failed
- Show compiler diagnostics (errors/warnings)
- Suggest missing include paths or macros
- Exit with `ToolingError`
- **Do not produce partial artifacts**

Example error:
```
ToolingError: Header compilation failed:
Error: test.h:10:5: unknown type name 'HANDLE'
Note: Did you include windows.h?
```

### Missing libclang
If libclang is not installed:
```
ImportError: libclang not found. Install with: pip install libclang
On Windows, ensure LLVM is installed and libclang.dll is available.
```

### Unknown Source Locations
If source location cannot be determined:
```json
{
  "file": "<unknown>",
  "line": 0,
  "column": 0
}
```

---

## Usage Examples

### Standalone Invocation
```bash
# Through orchestrator
python polyglot_ffi_verifier.py ingest interface.h library.dll

# Direct usage
python -c "
from src.core.execution_context import ExecutionContextBuilder
from src.ingestion import NativeInterfaceAnalyzer

builder = ExecutionContextBuilder()
context = builder.build('library.dll', '.')

analyzer = NativeInterfaceAnalyzer()
artifact = analyzer.analyze('interface.h', 'library.dll', context)
analyzer.save_artifact(artifact, 'artifacts/native_interface.json')
"
```

### Inspecting Output
```bash
# Pretty-print artifact
python -m json.tool artifacts/native_interface.json

# Extract function names
python -c "
import json
with open('artifacts/native_interface.json') as f:
    artifact = json.load(f)
    for func in artifact['functions']:
        print(func['name'])
"
```

---

## Known Limitations

### v1.0 Does NOT Support
- **C++ features** - Only C headers are supported
  - Workaround: Use `extern "C"` blocks
- **Complex macros** - Macros are not expanded
- **Variadic macros** - Not fully supported
- **Inline functions** - Only declarations extracted
- **Bitfields** - Not yet implemented
- **Flexible array members** - Not yet implemented

### Future Extensions
- C++ support via separate analyzer
- Macro expansion and evaluation
- Bitfield layout computation
- Flexible array member handling
- Cross-platform support (Linux, macOS)

---

## Validation

Run comprehensive validation:
```bash
python validate_ingestion.py
```

**Expected Output**:
```
======================================================================
  Native Interface Ingestion Validation
======================================================================

Testing ExecutionContext Integration...
  ✓ ExecutionContext integration working

Testing Simple Header Parsing...
  ✓ Simple header parsing successful

Testing Struct Layout with Padding...
  ✓ Struct layout with padding correct

Testing Enum Extraction...
  ✓ Enum extraction working

Testing Typedef Extraction...
  ✓ Typedef extraction working

Testing Calling Convention Detection...
  ✓ Calling convention detection working

Testing Source Location Tracking...
  ✓ Source location tracking working

Testing Provenance Metadata...
  ✓ Provenance metadata complete

======================================================================
  ✓ ALL TESTS PASSED (8/8)
======================================================================
```

---

## Artifact Schema

Complete schema for `native_interface.json`:

```json
{
  "provenance": {
    "producing_phase": "Native Interface Ingestion",
    "execution_id": "<UUID from ExecutionContext>",
    "timestamp": "<ISO 8601 UTC>",
    "tool_version": "1.0.0",
    "schema_version": "1.0.0",
    "input_artifacts": ["<header path>", "<library path>"],
    "compiler_invocation": "<full clang command>"
  },
  "platform": {
    "os_name": "Windows",
    "architecture": "AMD64",
    "pointer_width": 64,
    "endianness": "little"
  },
  "functions": [...],
  "structs": [...],
  "enums": [...],
  "typedefs": [...]
}
```

See specification for complete field details.

---

## Integration with Orchestration Layer

### ExecutionContext Usage
```python
# Read compiler configuration
compiler_path = context.compiler.compiler_path
include_paths = context.compiler.include_paths
macros = context.compiler.preprocessor_macros

# Read platform information
os_name = context.platform.os_name
architecture = context.platform.architecture

# Use execution ID for provenance
execution_id = context.provenance.execution_id
```

### Artifact Output
```python
# Write to artifacts directory
output_path = "artifacts/native_interface.json"
analyzer.save_artifact(artifact, output_path)
```

---

## Status

✅ **COMPLETE AND VALIDATED**

All requirements implemented:
- libclang integration working on Windows
- Struct layout with explicit padding
- Calling convention detection
- Complete provenance tracking
- All 8 validation tests passing

**Ready for Phase 3: IR Normalization**
