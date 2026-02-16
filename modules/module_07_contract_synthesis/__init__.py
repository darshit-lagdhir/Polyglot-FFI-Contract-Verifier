"""
Module 07: Contract Synthesis Engine
====================================

Transforms IR artifacts (structural compiler truth) into enforceable FFI 
contracts (runtime semantic expectations) through deterministic, conservative 
semantic projection.

The synthesis engine bridges Module 05 (IR Normalization) and Module 06 
(Contract Schema), applying rule-based transformations with complete 
traceability and versioning.

Key Features
------------
- Deterministic Synthesis: Identical input -> identical output
- Conservative Safety: Strict defaults unless proven otherwise
- Contextual Intelligence: Interface-wide pattern analysis
- Complete Traceability: Every clause links to IR entities
- Versioning System: Rule evolution tracking
- CLI Interface: Developer-friendly command-line tools

Quick Start
-----------
Synthesize contract from IR file:

>>> from module_07_contract_synthesis import synthesize_from_ir
>>> contract = synthesize_from_ir('interface.json')
>>> print(f"Generated {len(contract.clauses)} clauses")

Using the synthesis engine directly:

>>> from module_07_contract_synthesis import SynthesisEngine, SynthesisConfig
>>> config = SynthesisConfig(synthesis_version='1.0.0')
>>> engine = SynthesisEngine(config)
>>> result = engine.synthesize(ir_unit, 'my_interface')
>>> if result.success:
...     print(f"Success: {result.clauses_generated} clauses")

Command-Line Interface
----------------------
After installation, use the CLI:

$ pfcv-synth synthesize input.json -o contract.json
$ pfcv-synth validate contract.json
$ pfcv-synth batch interfaces/*.json --output-dir contracts/

Components
----------
- Core Synthesis: SynthesisEngine, SynthesisConfig, SynthesisResult
- Bridges: IRBridge, ContractBridge
- Versioning: RuleRegistry, version_compare, DeterminismVerifier
- CLI: main, cli

For detailed documentation, see: https://docs.pfcv.dev/modules/module-07-contract-synthesis
"""

import sys
import importlib
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from pathlib import Path

# Version metadata (import from single source)
from .version import (
    version,
    version_info,
    synthesis_version,
    title,
    description,
    url,
    author,
    author_email,
    license,
    copyright,
)

# Metadata aliases (Standard naming)
__version__ = version
__version_info__ = version_info
__synthesis_version__ = synthesis_version
__title__ = title
__description__ = description
__url__ = url
__author__ = author
__author_email__ = author_email
__license__ = license
__copyright__ = copyright

if TYPE_CHECKING:
    # Type checking imports (not runtime)
    from .synthesis_engine import (
        SynthesisEngine,
        SynthesisConfig,
        SynthesisResult,
        ClauseProvenance,
    )
    from .ir_bridge import IRBridge, IRValidator
    from .contract_bridge import ContractBridge
    from .versioning import (
        RuleRegistry,
        SynthesisRule,
        version_compare,
        DeterminismVerifier,
        RegressionDetector,
        FingerprintComputer,
    )
    from .cli import main, cli

# ============================================================================
# LAZY IMPORT CONFIGURATION
# ============================================================================

_lazy_imports = {
    # Core synthesis
    'SynthesisEngine': '.synthesis_engine',
    'SynthesisConfig': '.synthesis_engine',
    'SynthesisResult': '.synthesis_engine',
    'ClauseProvenance': '.synthesis_engine',
    
    # Bridges
    'IRBridge': '.ir_bridge',
    'IRValidator': '.ir_bridge',
    'ContractBridge': '.contract_bridge',
    
    # Versioning
    'RuleRegistry': '.versioning',
    'SynthesisRule': '.versioning',
    'version_compare': '.versioning',
    'DeterminismVerifier': '.versioning',
    'RegressionDetector': '.versioning',
    'FingerprintComputer': '.versioning',
    
    # CLI
    'main': '.cli',
    'cli': '.cli',
}

def __getattr__(name: str) -> Any:
    """
    Lazy import module attributes.
    
    Implements PEP 562 for lazy loading of heavy modules.
    """
    if name in _lazy_imports:
        module_path = _lazy_imports[name]
        
        # Handle relative imports
        if module_path.startswith('.'):
            module_path = __name__ + module_path
        
        module = importlib.import_module(module_path)
        attr = getattr(module, name)
        
        # Cache in module namespace
        globals()[name] = attr
        return attr
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__() -> List[str]:
    """List available attributes (for autocomplete)."""
    return sorted(list(_lazy_imports.keys()) + list(globals().keys()))

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def synthesize_from_ir(ir_path: Union[str, Path], config: Optional[Any] = None, strict: bool = True) -> Any:
    """
    Convenience function to synthesize contract from IR file.
    
    This is a high-level wrapper that handles file I/O, validation, and
    synthesis in one call.
    
    Args:
        ir_path: Path to IR JSON file (str or Path)
        config: Optional SynthesisConfig instance
        strict: If True, fail on validation errors
        
    Returns:
        ContractDocument instance
        
    Raises:
        IRBridgeError: If IR validation fails
        SynthesisError: If synthesis fails
        FileNotFoundError: If IR file doesn't exist
        
    Example:
        >>> contract = synthesize_from_ir('my_interface.json')
        >>> print(contract.header.target_interface_id)
        'my_interface'
    """
    # Lazy imports for the implementation
    from .synthesis_engine import SynthesisEngine, SynthesisConfig
    from module_05_ir_normalization.ir_serialization import IRSerializer
    
    ir_path = Path(ir_path)
    if not ir_path.exists():
        raise FileNotFoundError(f"IR file not found: {ir_path}")
    
    ir_serializer = IRSerializer()
    ir_unit = ir_serializer.deserialize(ir_path.read_text(encoding='utf-8'))
    
    # Setup synthesis
    if config is None:
        config = SynthesisConfig()
    
    engine = SynthesisEngine(config)
    
    # Synthesize
    result = engine.synthesize(ir_unit, ir_path.stem)
    
    if not result.success:
        error_msg = "\n".join(result.errors)
        raise RuntimeError(f"Synthesis failed:\n{error_msg}")
    
    return result.contract

def synthesize_from_file(ir_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None, format: str = 'json', config: Optional[Any] = None) -> Any:
    """
    Synthesize contract and write to file.
    
    Convenience function that synthesizes and serializes in one call.
    
    Args:
        ir_path: Path to IR JSON file
        output_path: Path for output contract file (optional)
        format: Output format ('json' or 'yaml')
        config: Optional SynthesisConfig instance
        
    Returns:
        ContractDocument instance
        
    Example:
        >>> contract = synthesize_from_file('input.json', 'output.json')
    """
    from module_06_contract_schema.contract_serialization import ContractSerializer
    
    # Synthesize
    contract = synthesize_from_ir(ir_path, config)
    
    # Serialize if output path provided
    if output_path:
        output_path = Path(output_path)
        serializer = ContractSerializer()
        
        if format == 'json':
            content = serializer.serialize(contract)
        elif format == 'yaml':
            import yaml
            import json
            # Convert to dict for YAML
            contract_dict = json.loads(serializer.serialize(contract))
            content = yaml.dump(contract_dict)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        output_path.write_text(content, encoding='utf-8')
    
    return contract

def validate_contract(contract_path: Union[str, Path]) -> bool:
    """
    Validate contract file.
    
    Convenience function for contract validation.
    
    Args:
        contract_path: Path to contract JSON file
        
    Returns:
        True if valid
        
    Raises:
        RuntimeError: If contract is invalid
        
    Example:
        >>> is_valid = validate_contract('contract.json')
    """
    from module_06_contract_schema.contract_serialization import ContractSerializer
    from module_06_contract_schema.contract_validation import ContractValidator
    
    contract_path = Path(contract_path)
    serializer = ContractSerializer()
    contract = serializer.deserialize(contract_path.read_text(encoding='utf-8'))
    
    validator = ContractValidator()
    result = validator.validate(contract)
    
    if hasattr(result, 'passed') and not result.passed:
        # Compatibility with different validation report structures
        errors = result.get_all_errors() if hasattr(result, 'get_all_errors') else []
        error_msg = "\n".join(errors)
        raise RuntimeError(f"Contract validation failed:\n{error_msg}")
    elif hasattr(result, 'is_valid') and not result.is_valid:
        error_msg = "\n".join(getattr(result, 'errors', []))
        raise RuntimeError(f"Contract validation failed:\n{error_msg}")
        
    return True

# ============================================================================
# PUBLIC API DEFINITION
# ============================================================================

__all__ = [
    # Version metadata
    'version',
    'version_info',
    'synthesis_version',
    'title',
    'description',
    'author',
    'license',
    
    # Core synthesis classes
    'SynthesisEngine',
    'SynthesisConfig',
    'SynthesisResult',
    'ClauseProvenance',
    
    # Bridge classes
    'IRBridge',
    'IRValidator',
    'ContractBridge',
    
    # Versioning
    'RuleRegistry',
    'SynthesisRule',
    'version_compare',
    'DeterminismVerifier',
    'RegressionDetector',
    'FingerprintComputer',
    
    # CLI
    'main',
    'cli',
    
    # Convenience functions
    'synthesize_from_ir',
    'synthesize_from_file',
    'validate_contract',
]
