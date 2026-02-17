"""Best practices for adapter integration."""

from typing import Any, Callable, List
from modules.module_08_language_adapter import (
    PythonAdapterComplete,
    ContractViolationError,
    NativeCrashError,
    EnforcementScope,
)

class BestPracticesGuide:
    """
    Demonstrates best practices for adapter integration.
    """

    @staticmethod
    def pattern_factory_function(contract_path: str) -> PythonAdapterComplete:
        """
        Pattern: Factory function for adapter creation.
        
        Centralizes configuration and initialization.
        """
        adapter = PythonAdapterComplete()
        adapter.load_contract(contract_path)
        adapter.enable_caching()
        adapter.enable_diagnostic_mode()
        return adapter

    @staticmethod
    def pattern_context_manager(adapter: PythonAdapterComplete, func_name: str):
        """
        Pattern: Context manager for resource safety.
        
        Ensures cleanup even on errors.
        """
        # Note: EnforcementScope is typically used within the adapter's implementation
        # of call_with_enforcement or provided via enforcement_scope() method.
        with adapter.enforcement_scope(func_name) as scope:
            buffer = bytearray(1024)
            # Add buffer to scope for tracking/pinning
            scope.add_buffer(buffer)
            
            # Resources automatically cleaned up on exit
            # Actual invocation would go here
            return True

    @staticmethod
    def pattern_error_handling(adapter: PythonAdapterComplete):
        """
        Pattern: Comprehensive error handling.
        
        Distinguishes between validation errors and native crashes.
        """
        try:
            # Demonstration of a call
            result = adapter.call_with_enforcement('my_function', 42)
            return result
        
        except ContractViolationError as e:
            # Handle contract violation (logic error in inputs/state)
            print(f"Contract violation: {e}")
            # Log violation for audit or return default
            return None
        
        except NativeCrashError as e:
            # Handle native crash (segfault, access violation)
            print(f"Native crash occurred: {e}")
            # Critical error, typically requires restart or alerting
            raise

    @staticmethod
    def pattern_batch_processing(
        adapter: PythonAdapterComplete,
        items: List[Any]
    ):
        """
        Pattern: Batch processing with performance tracking.
        
        Processes multiple items efficiently.
        """
        # Diagnostics can be enabled for the duration of batch
        adapter.enable_diagnostic_mode()
        results = []
        
        for item in items:
            try:
                result = adapter.call_with_enforcement('process', item)
                results.append(result)
            except Exception as e:
                print(f"Error processing {item}: {e}")
                results.append(None)
        
        # Get performance report if optimization manager is available
        if hasattr(adapter, 'optimization_manager'):
            report = adapter.optimization_manager.get_statistics()
            print(f"Processed {len(items)} items")
            print(f"Cache hit rate: {report.get('validation_cache', {}).get('hit_rate', 0)}")
        
        return results
