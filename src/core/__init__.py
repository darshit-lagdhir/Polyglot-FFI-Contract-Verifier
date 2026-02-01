"""
Core module for Polyglot FFI Contract Verifier.

This module contains the foundational components including execution context,
orchestration, and pipeline coordination.
"""

from .execution_context import (
    ExecutionContext,
    ExecutionContextBuilder,
    PlatformIdentification,
    CompilerInformation,
    NativeLibraryInformation,
    TargetLanguageRuntime,
    VerificationConfiguration,
    ProvenanceMetadata,
    ArtifactPaths
)

__all__ = [
    'ExecutionContext',
    'ExecutionContextBuilder',
    'PlatformIdentification',
    'CompilerInformation',
    'NativeLibraryInformation',
    'TargetLanguageRuntime',
    'VerificationConfiguration',
    'ProvenanceMetadata',
    'ArtifactPaths'
]
