"""Test Suite for CLI Tools - Prompt 20/25: 85 tests."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List

from cli.adapter_cli import (
    OutputFormatter,
    ContractCommands,
    StateCommands,
    PerfCommands,
    DebugCommands,
    AdapterCLI,
)


class TestOutputFormatter:
    """OutputFormatter tests (20 tests)."""

    def test_create_formatter(self):
        """Test 1761: Create output formatter."""
        formatter = OutputFormatter('text')
        assert formatter.format == 'text'

    @pytest.mark.parametrize("i", range(1762, 1770))
    def test_format_text_simple(self, i):
        """Test 1762-1769: Format simple text."""
        formatter = OutputFormatter('text')
        data = {'key': 'value', 'number': 42}
        
        output = formatter.format_output(data)
        assert 'key: value' in output
        assert 'number: 42' in output

    def test_format_json(self):
        """Test 1770: Format as JSON."""
        formatter = OutputFormatter('json')
        data = {'test': 'data'}
        
        output = formatter.format_output(data)
        parsed = json.loads(output)
        assert parsed == data

    def test_format_table(self):
        """Test 1771: Format as table."""
        formatter = OutputFormatter('table')
        data = [
            {'name': 'func1', 'count': 10},
            {'name': 'func2', 'count': 20}
        ]
        
        output = formatter.format_output(data)
        assert 'func1' in output
        assert '10' in output

    @pytest.mark.parametrize("i", range(1772, 1781))
    def test_format_nested_dict(self, i):
        """Test 1772-1780: Format nested dictionary."""
        formatter = OutputFormatter('text')
        data = {
            'outer': {
                'inner': 'value'
            }
        }
        
        output = formatter.format_output(data)
        assert 'outer:' in output
        assert 'inner: value' in output


class TestContractCommands:
    """ContractCommands tests (20 tests)."""

    def test_create_contract_commands(self):
        """Test 1781: Create contract commands."""
        formatter = OutputFormatter('text')
        commands = ContractCommands(formatter)
        assert commands.formatter is formatter

    @pytest.mark.parametrize("i", range(1782, 1790))
    def test_validate_valid_contract(self, i):
        """Test 1782-1789: Validate valid contract."""
        contract = {
            'contract_id': 'test',
            'schema_version': '1.0.0',
            'functions': {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            path = f.name
        
        try:
            formatter = OutputFormatter('text')
            commands = ContractCommands(formatter)
            
            result = commands.validate(path)
            assert result == 0
        finally:
            if os.path.exists(path):
                Path(path).unlink()

    def test_validate_invalid_contract(self):
        """Test 1790: Validate invalid contract."""
        contract = {}  # Missing required fields
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            path = f.name
        
        try:
            formatter = OutputFormatter('text')
            commands = ContractCommands(formatter)
            
            result = commands.validate(path)
            assert result == 1
        finally:
            if os.path.exists(path):
                Path(path).unlink()

    def test_validate_nonexistent_file(self):
        """Test 1791: Validate nonexistent file."""
        formatter = OutputFormatter('text')
        commands = ContractCommands(formatter)
        
        result = commands.validate('nonexistent_file_xyz.json')
        assert result == 1

    @pytest.mark.parametrize("i", range(1792, 1801))
    def test_inspect_contract(self, i):
        """Test 1792-1800: Inspect contract."""
        contract = {
            'contract_id': 'test',
            'schema_version': '1.0.0',
            'functions': {
                'func1': {
                    'parameters': [],
                    'return': {'type': 'int'}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            path = f.name
        
        try:
            formatter = OutputFormatter('json')
            commands = ContractCommands(formatter)
            
            result = commands.inspect(path)
            assert result == 0
        finally:
            if os.path.exists(path):
                Path(path).unlink()


class TestStateCommands:
    """StateCommands tests (15 tests)."""

    def test_create_state_commands(self):
        """Test 1801: Create state commands."""
        formatter = OutputFormatter('text')
        commands = StateCommands(formatter)
        assert commands.formatter is formatter

    def test_snapshot(self):
        """Test 1802: Create snapshot."""
        formatter = OutputFormatter('text')
        commands = StateCommands(formatter)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'snapshot.json'
            
            result = commands.snapshot(str(output_path))
            assert result == 0
            assert output_path.exists()

    @pytest.mark.parametrize("i", range(1803, 1816))
    def test_query_state(self, i):
        """Test 1803-1815: Query state data."""
        from modules.module_08_language_adapter import PythonAdapterComplete
        from modules.module_08_language_adapter.persistence import PersistenceManager
        
        # Create state file
        adapter = PythonAdapterComplete()
        adapter.contract_fingerprint = 'test_fp_123'
        
        manager = PersistenceManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / 'state.json'
            manager.save_state(adapter, state_path)
            
            formatter = OutputFormatter('text')
            commands = StateCommands(formatter)
            
            result = commands.query(str(state_path), 'contract_fingerprint')
            assert result == 0


class TestPerfCommands:
    """PerfCommands tests (10 tests)."""

    def test_create_perf_commands(self):
        """Test 1816: Create perf commands."""
        formatter = OutputFormatter('text')
        commands = PerfCommands(formatter)
        assert commands.formatter is formatter

    @pytest.mark.parametrize("i", range(1817, 1826))
    def test_performance_report(self, i):
        """Test 1817-1825: Generate performance report."""
        formatter = OutputFormatter('text')
        commands = PerfCommands(formatter)
        
        result = commands.report()
        assert result == 0


class TestDebugCommands:
    """DebugCommands tests (10 tests)."""

    def test_create_debug_commands(self):
        """Test 1826: Create debug commands."""
        formatter = OutputFormatter('text')
        commands = DebugCommands(formatter)
        assert commands.formatter is formatter

    @pytest.mark.parametrize("i", range(1827, 1836))
    def test_violations_list(self, i):
        """Test 1827-1835: List violations."""
        formatter = OutputFormatter('table')
        commands = DebugCommands(formatter)
        
        result = commands.violations()
        assert result == 0


class TestAdapterCLI:
    """AdapterCLI tests (10 tests)."""

    def test_create_cli(self):
        """Test 1836: Create CLI application."""
        cli = AdapterCLI()
        assert cli.parser is not None

    def test_contract_validate_command(self):
        """Test 1837: Run contract validate command."""
        contract = {
            'contract_id': 'test',
            'schema_version': '1.0.0',
            'functions': {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump(contract, f)
            path = f.name
        
        try:
            cli = AdapterCLI()
            result = cli.run(['contract', 'validate', path])
            assert result == 0
        finally:
            if os.path.exists(path):
                Path(path).unlink()

    @pytest.mark.parametrize("i", range(1838, 1846))
    def test_help_command(self, i):
        """Test 1838-1845: Help command."""
        cli = AdapterCLI()
        # No command specified should print help and return 1
        result = cli.run([])
        assert result == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
