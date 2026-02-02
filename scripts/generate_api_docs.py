#!/usr/bin/env python3
"""
Generate API documentation from docstrings.

Creates markdown documentation from module docstrings.
"""

import inspect
import importlib
import sys
import os
from pathlib import Path
from typing import Any

# Ensure we can import the module
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Mock libclang if needed for doc generation
try:
    import clang.cindex
except ImportError:
    # Very basic mock to allow import of verification_pipeline for docs
    class Mock:
            pass
    sys.modules['clang'] = Mock()
    sys.modules['clang.cindex'] = Mock()

def extract_signature(func: Any) -> str:
    """Extract function signature."""
    try:
        sig = inspect.signature(func)
        return f"{func.__name__}{sig}"
    except:
        return func.__name__ + "()"

def extract_docstring(obj: Any) -> str:
    """Extract and format docstring."""
    doc = inspect.getdoc(obj)
    return doc if doc else "No documentation available."

def generate_function_doc(name: str, func: Any) -> str:
    """Generate markdown for a function."""
    md = []
    md.append(f"### `{extract_signature(func)}`\n")
    md.append(extract_docstring(func))
    md.append("\n")
    return "\n".join(md)

def generate_class_doc(name: str, cls: Any) -> str:
    """Generate markdown for a class."""
    md = []
    md.append(f"## class `{name}`\n")
    md.append(extract_docstring(cls))
    md.append("\n")
    
    # Document methods
    for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not method_name.startswith('_'):
            md.append(f"#### `{name}.{method_name}()`\n")
            md.append(extract_docstring(method))
            md.append("\n")
    
    return "\n".join(md)

def generate_module_docs(module_name: str) -> str:
    """Generate complete module documentation."""
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        return f"# Error generating documentation for {module_name}\n\n{str(e)}"
    
    md = []
    md.append(f"# API Reference: {module_name}\n")
    md.append(f"{inspect.getdoc(module) if inspect.getdoc(module) else ''}\n\n")
    
    # Extract public API
    members = inspect.getmembers(module)
    
    # Functions
    md.append("## Functions\n")
    for name, obj in members:
        if inspect.isfunction(obj) and not name.startswith('_'):
            md.append(generate_function_doc(name, obj))
    
    # Classes
    md.append("## Classes\n")
    for name, obj in members:
        if inspect.isclass(obj) and not name.startswith('_'):
            # Only include classes defined in this module
            if obj.__module__ == module_name:
                md.append(generate_class_doc(name, obj))
    
    return "\n".join(md)

if __name__ == "__main__":
    # Target module
    module_target = "modules.module_02_verification_pipeline.verification_pipeline"
    
    # Generate API docs
    api_docs = generate_module_docs(module_target)
    
    # Write to file
    output_path = ROOT_DIR / "docs" / "API_REFERENCE_AUTO.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(api_docs, encoding='utf-8')
    
    print(f"✓ Generated API documentation: {output_path}")
