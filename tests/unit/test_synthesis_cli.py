"""
Tests for Module 07: CLI Interface (Prompt 6/15)
Testing Level: MEDIUM (80 tests)
"""

import pytest
import json
import logging
from pathlib import Path
from click.testing import CliRunner
from click.testing import CliRunner
# Defer cli import to avoid module level issues during collection if any


# ============================================================================
# TEST CLI BASIC FUNCTIONALITY
# ============================================================================

class TestCLIBasic:
    """Test basic CLI functionality."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_ir_file(self, tmp_path):
        """Create sample IR file."""
        ir_data = {
            "unit_id": "test",
            "types": [],
            "functions": []
        }
        
        ir_file = tmp_path / "test.json"
        ir_file.write_text(json.dumps(ir_data))
        return ir_file

    def test_cli_help(self, runner):
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'PFCV Contract Synthesis CLI' in result.output

    def test_cli_version(self, runner):
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_synthesize_command_exists(self, runner):
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, ['synthesize', '--help'])
        assert result.exit_code == 0
        assert 'Synthesize contract' in result.output

# ============================================================================
# TEST SYNTHESIZE COMMAND
# ============================================================================

# import module_05_ir_normalization.ir_entities as ir_ent
# from module_05_ir_normalization.ir_serialization import IRSerializer

class TestSynthesizeCommand:
    """Test synthesize command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def complete_ir_file(self, tmp_path):
        """Create complete IR file."""
        import module_05_ir_normalization.ir_entities as ir_ent
        from module_05_ir_normalization.ir_serialization import IRSerializer
        
        # Create InterfaceUnit
        ir_unit = ir_ent.InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=ir_ent.Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="10.0"
        )
        # Note: ID generated in post_init but better to set explicitly if mocked?
        # Actually post_init runs on init.

        # Create Struct
        struct = ir_ent.StructureType(
            structure_name="struct Point",
            size_bytes=8,
            alignment_bytes=4, # Correct arg name
            is_packed=False
        )
        # Manually trigger ID generation if needed or just use what's generated
        # Struct ID usually hash of name/content. 
        # But for test simplicity, we can trust auto generation.
        
        ir_unit.types.append(struct)
        
        # Create Return Entity
        # PointerType referring to struct
        ptr_type = ir_ent.PointerType(
            pointer_depth=1,
            pointer_width=64,
            target_type_reference=struct.entity_id
        )
        ir_unit.types.append(ptr_type) # Must register pointer type too? Yes.

        ret_entity = ir_ent.ReturnEntity(
             type_reference=ptr_type.entity_id,
             return_mechanism=ir_ent.ReturnMechanism.DIRECT
        )

        # Create Function
        func = ir_ent.FunctionSymbol(
            linkage_name="get_point",
            source_name="get_point",
            calling_convention=ir_ent.CallingConvention.CDECL,
            return_entity=ret_entity,
            parameters=[]
        )
        
        # symbols list contains FunctionSymbol and VariableSymbol
        ir_unit.symbols.append(func)
        
        serializer = IRSerializer()
        content = serializer.serialize(ir_unit)
        
        ir_file = tmp_path / "complete.json"
        ir_file.write_text(content)
        return ir_file

    def test_synthesize_with_output_file(self, runner, complete_ir_file, tmp_path):
        from module_07_contract_synthesis.cli import cli
        output_file = tmp_path / "contract.json"
        
        result = runner.invoke(cli, [
            'synthesize',
            str(complete_ir_file),
            '--output', str(output_file),
            '--format', 'json'
        ])
        
        if result.exit_code != 0:
            print(result.output)
            
        assert result.exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "contract" in content

    def test_synthesize_text_format(self, runner, complete_ir_file):
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, [
            'synthesize',
            str(complete_ir_file),
            '--format', 'text'
        ])
        
        assert result.exit_code == 0
        assert 'Synthesis Report' in result.output

# ============================================================================
# TEST BATCH COMMAND
# ============================================================================

class TestBatchCommand:
    """Test batch processing command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def multiple_ir_files(self, tmp_path):
        """Create multiple IR files."""
        ir_dir = tmp_path / "ir"
        ir_dir.mkdir()
        
        import module_05_ir_normalization.ir_entities as ir_ent
        from module_05_ir_normalization.ir_serialization import IRSerializer

        files = []
        for i in range(3):
            ir_unit = ir_ent.InterfaceUnit(
                target_architecture="x86_64",
                operating_system="linux",
                pointer_width=64,
                endianness=ir_ent.Endianness.LITTLE, 
                abi_mode="sysv", 
                compiler_family="gcc", compiler_version="10"
            )
            ir_unit.entity_id = f"test_{i}"
            
            serializer = IRSerializer()
            content = serializer.serialize(ir_unit)
            
            ir_file = ir_dir / f"test_{i}.json"
            ir_file.write_text(content)
            files.append(ir_file)
        
        return ir_dir, files

    def test_batch_processing(self, runner, multiple_ir_files, tmp_path):
        from module_07_contract_synthesis.cli import cli
        ir_dir, files = multiple_ir_files
        output_dir = tmp_path / "contracts"
        
        # Use glob pattern relative to test environment or absolute
        pattern = str(ir_dir / "*.json")
        
        result = runner.invoke(cli, [
            'batch',
            pattern,
            '--output-dir', str(output_dir),
            '--no-parallel' # Simplify testing
        ])
        
        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.json"))) == 3

# ============================================================================
# TEST DETERMINISM VERIFICATION
# ============================================================================

class TestDeterminismCommand:
    """Test determinism verification command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def simple_ir_file(self, tmp_path):
        import module_05_ir_normalization.ir_entities as ir_ent
        from module_05_ir_normalization.ir_serialization import IRSerializer

        ir_unit = ir_ent.InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=ir_ent.Endianness.LITTLE, 
            abi_mode="sysv", 
            compiler_family="gcc", compiler_version="10"
        )
        ir_unit.entity_id = "simple_det"
        
        serializer = IRSerializer()
        content = serializer.serialize(ir_unit)
        
        ir_file = tmp_path / "simple_det.json"
        ir_file.write_text(content)
        return ir_file

    def test_verify_determinism(self, runner, simple_ir_file):
        # We need to ensure mocked datetime if needed, but CLI runs in isolation usually?
        # CLI calls verify_determinism which uses normal logic.
        # If verify_determinism logic uses datetime.utcnow(), it will differ across runs if run spans seconds.
        # But verify_determinism runs in loop quickly.
        # The main issue is ContractHeader timestamp.
        # DeterminismVerifier logic should ideally mock or ignore timestamps if it wants to verify content stability.
        # Actually, DeterminismVerifier uses fingerprinting which might include timestamps if not careful.
        # Let's see if CLI mocks it or if we need to mock it here.
        
        # For this test, we accept real execution. If deterministic code is robust, it should pass.
        # If timestamp is part of fingerprint, it will fail.
        # Prompt 5 implementation of FingerprintComputer uses ContractSerializer.
        # ContractSerializer includes header.
        # If header has timestamp, fingerprint varies.
        # DeterminismVerifier runs synthesis multiple times.
        # If each run gets new timestamp, fingerprints differ.
        
        # To make this test pass, we likely need to mocking in test process.
        # Since CLI runs in process, patching works.
        from unittest.mock import patch
        
        with patch('module_06_contract_schema.contract_entities.datetime') as mock_dt, \
             patch('module_06_contract_schema.contract_serialization.datetime') as mock_dt2:
            
            from datetime import datetime
            fixed = datetime(2023, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = fixed
            mock_dt2.utcnow.return_value = fixed
            
            from module_07_contract_synthesis.cli import cli
            result = runner.invoke(cli, [
                'verify-determinism',
                str(simple_ir_file),
                '--iterations', '2'
            ])
        
        if result.exit_code != 0:
            print(result.output)
            
        assert result.exit_code == 0
        assert 'Deterministic' in result.output

# ============================================================================
# TEST DIFF COMMAND
# ============================================================================

class TestDiffCommand:
    """Test diff command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_diff_identical_contracts(self, runner, tmp_path):
        from module_07_contract_synthesis.cli import cli
        from module_06_contract_schema.contract_serialization import ContractSerializer
        from module_06_contract_schema.contract_entities import ContractDocument, ContractHeader
        import datetime

        # Create two identical contracts
        header = ContractHeader(
            target_interface_id="test",
            schema_version="1.0.0"
        )
        contract = ContractDocument(header=header, clauses=[])
        
        serializer = ContractSerializer()
        content = serializer.serialize(contract)
        
        file_a = tmp_path / "a.json"
        file_b = tmp_path / "b.json"
        file_a.write_text(content)
        file_b.write_text(content)
        
        result = runner.invoke(cli, ['diff', str(file_a), str(file_b)])
        
        assert result.exit_code == 0
        assert 'Contracts are identical' in result.output

# ============================================================================
# TEST EDGE CASES & ERROR HANDLING
# ============================================================================

class TestCLIEdgeCases:
    """Test CLI edge cases."""

    def test_nonexistent_file(self):
        from module_07_contract_synthesis.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ['synthesize', 'nonexistent.json'])
        assert result.exit_code != 0
        assert 'not exist' in result.output or 'No such file' in result.output

    def test_invalid_format_option(self):
        from module_07_contract_synthesis.cli import cli
        runner = CliRunner()
        # Create dummy file
        with runner.isolated_filesystem():
            with open("test.json", "w") as f: f.write("{}")
            result = runner.invoke(cli, ['synthesize', 'test.json', '--format', 'invalid'])
            assert result.exit_code != 0
            assert 'Invalid value for' in result.output

    @pytest.mark.parametrize("cmd", ["synthesize", "validate", "info", "verify-determinism"])
    def test_missing_argument(self, cmd):
        from module_07_contract_synthesis.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, [cmd])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output

    def test_info_on_invalid_json(self, tmp_path):
        from module_07_contract_synthesis.cli import cli
        runner = CliRunner()
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")
        
        result = runner.invoke(cli, ['info', str(bad_file)])
        assert result.exit_code != 0
        assert 'Error' in result.output

# ============================================================================
# COMPREHENSIVE COVERAGE (Parameterized)
# ============================================================================

class TestCLIComprehensive:
    """Parameterized tests to reach high coverage."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.mark.parametrize("flag", ["--verbose", "--quiet", "-v", "-q"])
    def test_global_options(self, runner, flag):
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, [flag, '--version'])
        assert result.exit_code == 0

    @pytest.mark.parametrize("fmt", ["json", "text"])
    def test_synthesize_formats(self, runner, fmt, tmp_path):
        # Already tested basically but confirming again with parameterization
        # We need a valid IR file
        import module_05_ir_normalization.ir_entities as ir_ent
        from module_05_ir_normalization.ir_serialization import IRSerializer
        
        ir_unit = ir_ent.InterfaceUnit(
            target_architecture="x86_64", operating_system="linux",
            pointer_width=64, endianness=ir_ent.Endianness.LITTLE,
            abi_mode="sysv", compiler_family="gcc", compiler_version="10"
        )
        ir_unit.entity_id = "test_fmt"
        
        ir_file = tmp_path / "ir.json"
        ir_file.write_text(IRSerializer().serialize(ir_unit))
        
        from module_07_contract_synthesis.cli import cli
        result = runner.invoke(cli, ['synthesize', str(ir_file), '--format', fmt])
        assert result.exit_code == 0
