"""
Polyglot FFI Contract Verifier

A developer-focused verification system for FFI boundaries.
"""

__version__ = '1.0.0'
__author__ = 'Darshit Lagdhir'

# Core components
from .context import ExecutionContext, ExecutionContextBuilder
from .pipeline import Pipeline

# Modules exposure (optional but good for library usage)
from .ingestion import NativeInterfaceAnalyzer
from .normalization import IRNormalizer
from .synthesis import ContractSynthesizer
from .adapters import AdapterGenerator
from .test_planning import TestPlanGenerator
from .execution import VerificationExecutor
from .diagnosis import DiagnosticMapper
from .reporting import ReportGenerator

# Public API
def verify(header_path: str, library_path: str, **kwargs):
    """
    One-line verification API.
    
    Args:
        header_path: Path to C header file
        library_path: Path to shared library
        **kwargs: Additional arguments passed to ExecutionContextBuilder.build
    """
    builder = ExecutionContextBuilder()
    if 'working_directory' not in kwargs:
        kwargs['working_directory'] = '.'
        
    context = builder.build(header_file=header_path, library_file=library_path, **kwargs)
    pipeline = Pipeline(context)
    return pipeline.execute_full_pipeline()

__all__ = [
    'ExecutionContext',
    'Pipeline',
    'verify',
    'NativeInterfaceAnalyzer',
    'IRNormalizer',
    'ContractSynthesizer',
    'AdapterGenerator',
    'TestPlanGenerator',
    'VerificationExecutor',
    'DiagnosticMapper',
    'ReportGenerator'
]
