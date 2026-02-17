"""Command-line interface for Language Adapter."""

import sys
import argparse
import json
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 105: OUTPUT FORMATTER
# ════════════════════════════════════════════════════════════════════════════

class OutputFormatter:
    """
    Formats CLI output in multiple formats.
    
    Supports text, JSON, and table formats.
    """

    def __init__(self, format: str = 'text'):
        self.format = format

    def format_output(self, data: Any) -> str:
        """
        Format data for output.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string
        """
        if self.format == 'json':
            return json.dumps(data, indent=2)
        
        elif self.format == 'table':
            return self._format_table(data)
        
        else:  # text
            return self._format_text(data)

    def _format_text(self, data: Any) -> str:
        """Format as human-readable text."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{key}:")
                    lines.append(self._indent(self._format_text(value)))
                else:
                    lines.append(f"{key}: {value}")
            return '\n'.join(lines)
        
        elif isinstance(data, list):
            if not data:
                return "[]"
            return '\n'.join(f"- {self._format_text(item)}" for item in data)
        
        else:
            return str(data)

    def _format_table(self, data: Any) -> str:
        """Format as table."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dicts -> table
            headers = list(data[0].keys())
            
            # Calculate column widths
            widths = {h: len(h) for h in headers}
            for row in data:
                for h in headers:
                    widths[h] = max(widths[h], len(str(row.get(h, ''))))
            
            # Build table
            lines = []
            
            # Header
            header_line = ' | '.join(h.ljust(widths[h]) for h in headers)
            lines.append(header_line)
            lines.append('-' * len(header_line))
            
            # Rows
            for row in data:
                row_line = ' | '.join(
                    str(row.get(h, '')).ljust(widths[h]) for h in headers
                )
                lines.append(row_line)
            
            return '\n'.join(lines)
        
        return self._format_text(data)

    def _indent(self, text: str, spaces: int = 2) -> str:
        """Indent text."""
        indent_str = ' ' * spaces
        return '\n'.join(indent_str + line for line in text.split('\n'))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 106: CONTRACT COMMANDS
# ════════════════════════════════════════════════════════════════════════════

class ContractCommands:
    """Contract management commands."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter

    def validate(self, contract_path: str) -> int:
        """
        Validate contract file.
        
        Args:
            contract_path: Path to contract file
            
        Returns:
            Exit code (0 = success)
        """
        try:
            with open(contract_path, 'r') as f:
                contract = json.load(f)
            
            # Basic validation
            errors = []
            
            if 'contract_id' not in contract:
                errors.append("Missing 'contract_id'")
            
            if 'schema_version' not in contract:
                errors.append("Missing 'schema_version'")
            
            if 'functions' not in contract:
                errors.append("Missing 'functions'")
            
            if errors:
                print("Validation failed:")
                for error in errors:
                    print(f"  ✗ {error}")
                return 1
            
            print("✓ Contract is valid")
            print(f"  Contract ID: {contract['contract_id']}")
            print(f"  Functions: {len(contract['functions'])}")
            return 0
        
        except FileNotFoundError:
            print(f"Error: Contract file not found: {contract_path}")
            return 1
        
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def inspect(self, contract_path: str) -> int:
        """
        Inspect contract details.
        
        Args:
            contract_path: Path to contract file
            
        Returns:
            Exit code
        """
        try:
            with open(contract_path, 'r') as f:
                contract = json.load(f)
            
            info = {
                'contract_id': contract.get('contract_id'),
                'schema_version': contract.get('schema_version'),
                'functions': []
            }
            
            for func_name, func_data in contract.get('functions', {}).items():
                func_info = {
                    'name': func_name,
                    'parameters': len(func_data.get('parameters', [])),
                    'return_type': func_data.get('return', {}).get('type', 'void')
                }
                info['functions'].append(func_info)
            
            print(self.formatter.format_output(info))
            return 0
        
        except Exception as e:
            print(f"Error: {e}")
            return 1

# ════════════════════════════════════════════════════════════════════════════
# SECTION 107: STATE COMMANDS
# ════════════════════════════════════════════════════════════════════════════

class StateCommands:
    """State inspection commands."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter

    def snapshot(self, output_path: str) -> int:
        """
        Create state snapshot.
        
        Args:
            output_path: Path to save snapshot
            
        Returns:
            Exit code
        """
        from modules.module_08_language_adapter import PythonAdapterComplete
        from modules.module_08_language_adapter.persistence import PersistenceManager
        
        try:
            # Create sample adapter (in real use, would connect to running adapter)
            adapter = PythonAdapterComplete()
            
            # Save snapshot
            manager = PersistenceManager()
            manager.save_state(adapter, output_path)
            
            print(f"✓ Snapshot saved to {output_path}")
            return 0
        
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def query(self, state_path: str, query_path: str) -> int:
        """
        Query state data.
        
        Args:
            state_path: Path to state file
            query_path: Query path (e.g., 'statistics.invocations')
            
        Returns:
            Exit code
        """
        from modules.module_08_language_adapter.persistence import PersistenceManager
        
        try:
            manager = PersistenceManager()
            state = manager.load_state(state_path)
            
            # Navigate query path
            parts = query_path.split('.')
            current = state
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    print(f"Error: Path not found: {query_path}")
                    return 1
            
            print(self.formatter.format_output(current))
            return 0
        
        except Exception as e:
            print(f"Error: {e}")
            return 1

# ════════════════════════════════════════════════════════════════════════════
# SECTION 108: PERFORMANCE COMMANDS
# ════════════════════════════════════════════════════════════════════════════

class PerfCommands:
    """Performance analysis commands."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter

    def report(self, metrics_path: Optional[str] = None) -> int:
        """
        Generate performance report.
        
        Args:
            metrics_path: Optional path to metrics file
            
        Returns:
            Exit code
        """
        # Sample metrics for demonstration
        metrics = {
            'total_invocations': 1000,
            'average_duration_ms': 2.5,
            'cache_hit_rate': 0.85,
            'validation_overhead_ms': 0.3
        }
        
        if self.formatter.format == 'text':
            print("Performance Report")
            print("=" * 50)
        
        print(self.formatter.format_output(metrics))
        return 0

# ════════════════════════════════════════════════════════════════════════════
# SECTION 109: DEBUG COMMANDS
# ════════════════════════════════════════════════════════════════════════════

class DebugCommands:
    """Debugging utilities."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter

    def violations(self, filter_str: Optional[str] = None) -> int:
        """
        Show violation history.
        
        Args:
            filter_str: Optional filter string
            
        Returns:
            Exit code
        """
        # Sample violations for demonstration
        violations = [
            {
                'function': 'process_buffer',
                'clause': 'range_check',
                'timestamp': '2024-01-15T10:30:00Z'
            },
            {
                'function': 'allocate',
                'clause': 'nullability',
                'timestamp': '2024-01-15T10:31:00Z'
            }
        ]
        
        if self.formatter.format == 'text':
            print("Recent Violations")
            print("=" * 50)
            
        print(self.formatter.format_output(violations))
        return 0

# ════════════════════════════════════════════════════════════════════════════
# SECTION 110: MAIN CLI APPLICATION
# ════════════════════════════════════════════════════════════════════════════

class AdapterCLI:
    """
    Main CLI application.
    
    Coordinates all commands and provides unified interface.
    """

    def __init__(self):
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser."""
        parser = argparse.ArgumentParser(
            prog='adapter-cli',
            description='Language Adapter CLI Tools'
        )
        
        parser.add_argument(
            '--format',
            choices=['text', 'json', 'table'],
            default='text',
            help='Output format'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Contract commands
        contract = subparsers.add_parser('contract', help='Contract management')
        contract_sub = contract.add_subparsers(dest='subcommand')
        
        validate = contract_sub.add_parser('validate', help='Validate contract')
        validate.add_argument('file', help='Contract file')
        
        inspect = contract_sub.add_parser('inspect', help='Inspect contract')
        inspect.add_argument('file', help='Contract file')
        
        # State commands
        state = subparsers.add_parser('state', help='State inspection')
        state_sub = state.add_subparsers(dest='subcommand')
        
        snapshot = state_sub.add_parser('snapshot', help='Create snapshot')
        snapshot.add_argument('output', help='Output file')
        
        query = state_sub.add_parser('query', help='Query state')
        query.add_argument('file', help='State file')
        query.add_argument('path', help='Query path')
        
        # Performance commands
        perf = subparsers.add_parser('perf', help='Performance analysis')
        perf_sub = perf.add_subparsers(dest='subcommand')
        
        report = perf_sub.add_parser('report', help='Performance report')
        report.add_argument('--metrics', help='Metrics file')
        
        # Debug commands
        debug = subparsers.add_parser('debug', help='Debugging utilities')
        debug_sub = debug.add_subparsers(dest='subcommand')
        
        violations = debug_sub.add_parser('violations', help='Show violations')
        violations.add_argument('--filter', help='Filter string')
        
        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI application.
        
        Args:
            args: Command-line arguments
            
        Returns:
            Exit code
        """
        parsed = self.parser.parse_args(args)
        
        # Create formatter
        formatter = OutputFormatter(parsed.format)
        
        # Route to command handler
        if parsed.command == 'contract':
            commands = ContractCommands(formatter)
            
            if parsed.subcommand == 'validate':
                return commands.validate(parsed.file)
            
            elif parsed.subcommand == 'inspect':
                return commands.inspect(parsed.file)
        
        elif parsed.command == 'state':
            commands = StateCommands(formatter)
            
            if parsed.subcommand == 'snapshot':
                return commands.snapshot(parsed.output)
            
            elif parsed.subcommand == 'query':
                return commands.query(parsed.file, parsed.path)
        
        elif parsed.command == 'perf':
            commands = PerfCommands(formatter)
            
            if parsed.subcommand == 'report':
                return commands.report(parsed.metrics if hasattr(parsed, 'metrics') else None)
        
        elif parsed.command == 'debug':
            commands = DebugCommands(formatter)
            
            if parsed.subcommand == 'violations':
                return commands.violations(parsed.filter if hasattr(parsed, 'filter') else None)
        
        # No command specified or unknown command
        self.parser.print_help()
        return 1

def main():
    """CLI entry point."""
    cli = AdapterCLI()
    sys.exit(cli.run())

if __name__ == '__main__':
    main()

__all__ = [
    'OutputFormatter',
    'ContractCommands',
    'StateCommands',
    'PerfCommands',
    'DebugCommands',
    'AdapterCLI',
]
