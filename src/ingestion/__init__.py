"""
Native Interface Ingestion Module

This module provides compiler-grade extraction of ABI information from C header files.
It uses libclang to parse headers and extract functions, structs, enums, and typedefs
with complete ABI details including struct layouts with explicit padding.

Components:
- NativeInterfaceAnalyzer: Main orchestrator for ingestion
- CompilerFrontend: libclang integration and AST parsing
- ABIExtractor: ABI-specific detail extraction (layouts, calling conventions)
- SourceLocationTracker: Source location tracking and formatting
"""

from .native_interface_analyzer import NativeInterfaceAnalyzer
from .compiler_frontend import CompilerFrontend
from .abi_extractor import ABIExtractor
from .source_location_tracker import SourceLocationTracker

__all__ = [
    'NativeInterfaceAnalyzer',
    'CompilerFrontend',
    'ABIExtractor',
    'SourceLocationTracker',
]
