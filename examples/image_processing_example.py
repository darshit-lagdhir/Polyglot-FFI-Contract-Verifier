# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: d6853f40814bc2f5
# ==============================================================================

"""Image Processing Integration Example."""

import json
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, Optional

from modules.module_08_language_adapter import PythonAdapterComplete
from modules.module_08_language_adapter.testing_utils import (
    MockFFIFunction,
    BehaviorSimulator,
)

class ImageProcessingExample:
    """
    Complete example of image processing with FFI enforcement.
    
    Demonstrates buffer management, ownership tracking, and error handling.
    """

    def __init__(self):
        self.adapter = PythonAdapterComplete()
        self.adapter.enable_diagnostic_mode()
        self._setup_contract()
        self._setup_mock_functions()

    def _setup_contract(self):
        """Setup contract for image processing functions."""
        contract = {
            'contract_id': 'image_processing',
            'schema_version': '1.0.0',
            'functions': {
                'load_image': {
                    'name': 'load_image',
                    'parameters': [
                        {
                            'name': 'path',
                            'type': 'char*',
                            'clauses': [
                                {
                                    'clause_id': 'path_not_null',
                                    'clause_type': 'nullability',
                                    'severity': 'mandatory',
                                    'metadata': {'allow_null': False}
                                }
                            ]
                        }
                    ],
                    'return': {'type': 'void*'}
                },
                'apply_filter': {
                    'name': 'apply_filter',
                    'parameters': [
                        {
                            'name': 'image',
                            'type': 'void*',
                            'clauses': []
                        },
                        {
                            'name': 'filter_type',
                            'type': 'int',
                            'clauses': [
                                {
                                    'clause_id': 'filter_range',
                                    'clause_type': 'range',
                                    'severity': 'mandatory',
                                    'metadata': {'min': 0, 'max': 10}
                                }
                            ]
                        }
                    ],
                    'return': {'type': 'int'}
                }
            }
        }
        
        # Save contract temporarily
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            self.contract_path = f.name
        
        try:
            self.adapter.load_contract(self.contract_path)
        finally:
            # We keep it for the lifetime of the object or delete after load
            # In real scenario, it would be a static file.
            pass

    def _setup_mock_functions(self):
        """Setup mock FFI functions for testing."""
        self.mock_load_image = MockFFIFunction(
            'load_image',
            BehaviorSimulator.return_value(0x1000)  # Mock image pointer
        )
        
        self.mock_apply_filter = MockFFIFunction(
            'apply_filter',
            BehaviorSimulator.return_value(0)  # Success
        )

    def process_image(self, image_path: str, filter_type: int) -> bool:
        """
        Process image with filter.
        
        Args:
            image_path: Path to image file
            filter_type: Filter type (0-10)
            
        Returns:
            True if successful
        """
        try:
            # Load image
            image_ptr = self.adapter.call_with_enforcement(
                'load_image',
                image_path,
                native_callable=self.mock_load_image
            )
            
            if image_ptr is None:
                return False
            
            # Apply filter
            result = self.adapter.call_with_enforcement(
                'apply_filter',
                image_ptr,
                filter_type,
                native_callable=self.mock_apply_filter
            )
            
            return result == 0
        
        except Exception as e:
            print(f"Error processing image: {e}")
            return False

    def get_performance_metrics(self):
        """Get performance metrics."""
        return self.adapter.get_performance_metrics()

    def __del__(self):
        """Cleanup temporary contract file."""
        if hasattr(self, 'contract_path') and os.path.exists(self.contract_path):
            try:
                os.unlink(self.contract_path)
            except OSError:
                pass


def run_image_processing_example():
    """Run image processing example."""
    example = ImageProcessingExample()

    # Process image with valid filter
    print("Running valid image processing...")
    success = example.process_image('/path/to/image.jpg', 5)
    print(f"Processing succeeded: {success}")

    # Try invalid filter (should fail validation)
    print("\nRunning invalid image processing (expecting validation error)...")
    try:
        example.process_image('/path/to/image.jpg', 99)
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Get metrics
    metrics = example.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"Total time: {metrics.get('total_time_ms', 0):.2f}ms")
    print(f"Invocations: {metrics.get('total_invocations', 0)}")


if __name__ == "__main__":
    run_image_processing_example()