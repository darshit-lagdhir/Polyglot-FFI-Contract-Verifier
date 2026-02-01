"""
Compiler Frontend

Interfaces with libclang to parse C header files and provide AST access.
Handles compiler invocation, error reporting, and Windows/MSVC-specific configuration.
"""

import os
import sys
from typing import List, Optional
from pathlib import Path

# Configure libclang before importing
def _configure_libclang():
    """
    Configure libclang library path for Windows.
    
    Searches common LLVM installation locations and sets library path.
    """
    common_paths = [
        r"C:\Program Files\LLVM\bin\libclang.dll",
        r"C:\Program Files (x86)\LLVM\bin\libclang.dll",
        r"C:\LLVM\bin\libclang.dll",
    ]
    
    # Check if LIBCLANG_PATH environment variable is set
    env_path = os.environ.get('LIBCLANG_PATH')
    if env_path and os.path.exists(env_path):
        import clang.cindex
        clang.cindex.Config.set_library_file(env_path)
        return
    
    # Search common paths
    for path in common_paths:
        if os.path.exists(path):
            import clang.cindex
            clang.cindex.Config.set_library_file(path)
            return
    
    # If not found, let clang.cindex try to find it automatically
    pass

# Configure before importing clang
_configure_libclang()

try:
    import clang.cindex as clang
except ImportError:
    raise ImportError(
        "libclang not found. Install with: pip install libclang\n"
        "On Windows, ensure LLVM is installed and libclang.dll is available."
    )

class CompilerFrontend:
    """
    Compiler frontend for parsing C headers using libclang.
    
    Responsibilities:
    - Configure libclang with correct compiler flags
    - Parse header files into AST
    - Validate compilation success
    - Provide AST access to analyzer
    - Report compilation errors clearly
    """
    
    def __init__(self):
        """Initialize compiler frontend with libclang index."""
        self.index = clang.Index.create()
    
    def parse_header(
        self,
        header_path: str,
        context
    ):
        """
        Parse a C header file using libclang.
        
        Args:
            header_path: Absolute path to header file
            context: ExecutionContext with compiler configuration
            
        Returns:
            libclang TranslationUnit (AST)
            
        Raises:
            ToolingError: If parsing fails or header has errors
        """
        # Validate header exists
        if not os.path.exists(header_path):
            from core.orchestration import ToolingError
            raise ToolingError(f"Header file not found: {header_path}")
        
        # Build compiler command arguments
        args = self.get_compiler_command(context)
        
        # Parse with libclang
        try:
            tu = self.index.parse(
                header_path,
                args=args,
                options=(
                    clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD |
                    clang.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
                )
            )
        except Exception as e:
            from core.orchestration import ToolingError
            raise ToolingError(f"Failed to parse header: {e}")
        
        # Validate compilation
        if not self.validate_compilation(tu):
            from core.orchestration import ToolingError
            diagnostics = self._format_diagnostics(tu)
            raise ToolingError(
                f"Header compilation failed:\n{diagnostics}"
            )
        
        return tu
    
    def get_compiler_command(self, context) -> List[str]:
        """
        Construct compiler command arguments from ExecutionContext.
        
        Args:
            context: ExecutionContext with compiler configuration
            
        Returns:
            List of compiler arguments for libclang
        """
        args = []
        
        # Add include paths
        for include_path in context.compiler.include_paths:
            args.append(f"-I{include_path}")
        
        # Add preprocessor macros
        for macro in context.compiler.preprocessor_macros:
            args.append(f"-D{macro}")
        
        # Add platform-specific flags
        if context.platform.os_name == "Windows":
            # MSVC compatibility flags
            args.extend([
                "-fms-compatibility",
                "-fms-extensions",
                f"-fms-compatibility-version={context.compiler.compiler_version}",
            ])
        
        # Add architecture flag
        if context.platform.architecture == "AMD64":
            args.append("-m64")
        
        return args
    
    def validate_compilation(self, tu) -> bool:
        """
        Validate that translation unit compiled without errors.
        
        Args:
            tu: libclang TranslationUnit
            
        Returns:
            True if no errors, False if errors present
            
        Important:
            Warnings are allowed, only errors cause validation failure
        """
        for diag in tu.diagnostics:
            if diag.severity >= clang.Diagnostic.Error:
                return False
        return True
    
    def _format_diagnostics(self, tu) -> str:
        """
        Format compilation diagnostics for error reporting.
        
        Args:
            tu: libclang TranslationUnit
            
        Returns:
            Formatted diagnostic messages
        """
        messages = []
        for diag in tu.diagnostics:
            severity = self._severity_name(diag.severity)
            location = diag.location
            if location.file:
                loc_str = f"{location.file.name}:{location.line}:{location.column}"
            else:
                loc_str = "<unknown>"
            
            messages.append(f"{severity}: {loc_str}: {diag.spelling}")
        
        return "\n".join(messages) if messages else "No diagnostics available"
    
    def _severity_name(self, severity) -> str:
        """Get human-readable severity name."""
        if severity == clang.Diagnostic.Ignored:
            return "Ignored"
        elif severity == clang.Diagnostic.Important:
            return "Note"
        elif severity == clang.Diagnostic.Warning:
            return "Warning"
        elif severity == clang.Diagnostic.Error:
            return "Error"
        elif severity == clang.Diagnostic.Fatal:
            return "Fatal"
        else:
            return "Unknown"
    
    def get_compiler_invocation_string(self, header_path: str, context) -> str:
        """
        Get full compiler command as string for provenance.
        
        Args:
            header_path: Path to header file
            context: ExecutionContext
            
        Returns:
            Full compiler command string
        """
        args = self.get_compiler_command(context)
        return f"clang {' '.join(args)} {header_path}"
