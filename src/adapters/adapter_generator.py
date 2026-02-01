"""
Adapter Generator
Orchestrates the generation of all adapter modules from an FFI contract.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from .struct_definition_generator import StructDefinitionGenerator
from .function_wrapper_generator import FunctionWrapperGenerator
from .exception_class_generator import ExceptionClassGenerator
from .ownership_tracker_generator import OwnershipTrackerGenerator

class AdapterGenerator:
    """
    Main orchestrator for Phase 6.
    """
    
    def __init__(self):
        self.struct_gen = StructDefinitionGenerator()
        self.func_gen = FunctionWrapperGenerator()
        self.exc_gen = ExceptionClassGenerator()
        self.own_gen = OwnershipTrackerGenerator()

    def generate(self, context) -> Dict[str, Any]:
        """
        Generates the full suite of Python adapters.
        """
        contract_path = context.artifacts.contract_path
        ir_path = context.artifacts.intermediate_representation_path
        
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contract artifact not found: {contract_path}")
        if not os.path.exists(ir_path):
            raise FileNotFoundError(f"IR artifact not found: {ir_path}")
            
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        with open(ir_path, 'r') as f:
            ir = json.load(f)

        lib_name = os.path.basename(context.native_library.library_path).split('.')[0]
        lib_path = context.native_library.library_path
        
        output_dir = os.path.join(context.artifacts.working_directory, "adapters")
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Generate Exceptions
        exc_code = self.exc_gen.generate_exception_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_exceptions.py"), "w") as f:
            f.write(exc_code)
            
        # 2. Generate Ownership Tracker
        own_code = self.own_gen.generate_ownership_module(lib_name)
        with open(os.path.join(output_dir, f"{lib_name}_ownership.py"), "w") as f:
            f.write(own_code)
            
        # 3. Generate Structs
        struct_code = self.struct_gen.generate_struct_module(lib_name, contract.get("struct_contracts", []), ir)
        with open(os.path.join(output_dir, f"{lib_name}_structs.py"), "w") as f:
            f.write(struct_code)
            
        # 4. Generate Main Adapter
        adapter_code = self.func_gen.generate_wrapper_module(lib_name, lib_path, contract.get("function_contracts", []))
        with open(os.path.join(output_dir, f"{lib_name}_adapter.py"), "w") as f:
            f.write(adapter_code)
            
        # 5. Generate __init__.py
        with open(os.path.join(output_dir, "__init__.py"), "w") as f:
            f.write(f"from . import {lib_name}_adapter as adapter\n")
            f.write(f"from . import {lib_name}_structs as structs\n")
            f.write(f"from . import {lib_name}_exceptions as exceptions\n")

        # 6. Generate Metadata
        metadata = {
            "provenance": {
                "producing_phase": "Phase 6: Language Adapter Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": "1.0.0",
                "schema_version": "1.0.0",
                "input_artifacts": [os.path.abspath(contract_path), os.path.abspath(ir_path)]
            },
            "target_language": "Python",
            "ffi_mechanism": "ctypes",
            "library_name": lib_name,
            "library_path": lib_path,
            "generated_modules": [
                f"adapters/{lib_name}_adapter.py",
                f"adapters/{lib_name}_structs.py",
                f"adapters/{lib_name}_exceptions.py",
                f"adapters/{lib_name}_ownership.py"
            ],
            "statistics": {
                "functions_wrapped": len(contract.get("function_contracts", [])),
                "structs_generated": len(contract.get("struct_contracts", [])),
                "constraints_enforced": self._count_constraints(contract),
                "constraints_skipped": 0
            }
        }
        
        metadata_path = os.path.join(output_dir, "adapter_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def _count_constraints(self, contract: Dict[str, Any]) -> int:
        count = 0
        for f in contract.get("function_contracts", []):
            count += len(f.get("pre_conditions", []))
            count += len(f.get("post_conditions", []))
        return count
