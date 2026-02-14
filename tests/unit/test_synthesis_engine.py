"""
Unit tests for Module 07: Synthesis Engine (Prompt 1/15)
Testing Level: EASY (50 tests)
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_07_contract_synthesis.synthesis_engine import (
    SynthesisConfig,
    ClauseProvenance,
    SynthesisResult,
    LayoutClauseGenerator,
    NullabilityClauseGenerator,
    OwnershipClauseGenerator,
    SynthesisEngine
)

from module_05_ir_normalization.ir_entities import (
    InterfaceUnit,
    TypeEntity,
    FunctionSymbol,
    ParameterEntity,
    EntityKind,
    StructureType,
    UnionType,
    PointerType,
    FieldEntity,
    ScalarType,
    ScalarKind,
    ReturnEntity,
    ReturnMechanism,
    CallingConvention,
    Endianness
)

from module_06_contract_schema.contract_entities import (
    Severity,
    ClauseType
)


# ============================================================================
# TEST SYNTHESIS CONFIG
# ============================================================================


class TestSynthesisConfig:
    """Test synthesis configuration."""

    def test_default_config_creation(self):
        config = SynthesisConfig()
        
        assert config.synthesis_version == "1.0.0"
        assert config.default_pointer_nonnull is True
        assert config.enable_layout_generation is True

    def test_custom_config_creation(self):
        config = SynthesisConfig(
            synthesis_version="2.0.0",
            default_pointer_nonnull=False,
            strict_mode=False
        )
        
        assert config.synthesis_version == "2.0.0"
        assert config.default_pointer_nonnull is False
        assert config.strict_mode is False

    def test_config_generator_toggles(self):
        config = SynthesisConfig(
            enable_layout_generation=False,
            enable_nullability_generation=False
        )
        
        assert config.enable_layout_generation is False
        assert config.enable_nullability_generation is False
        assert config.enable_ownership_generation is True


# ============================================================================
# TEST PROVENANCE TRACKING
# ============================================================================


class TestClauseProvenance:
    """Test provenance metadata."""

    def test_provenance_creation(self):
        prov = ClauseProvenance(
            ir_entity_id="struct Point",
            ir_entity_type="structure",
            rule_id="layout_projection",
            rule_version="1.0.0",
            confidence=1.0,
            explanation="Test provenance"
        )
        
        assert prov.ir_entity_id == "struct Point"
        assert prov.confidence == 1.0

    def test_provenance_to_dict(self):
        prov = ClauseProvenance(
            ir_entity_id="test",
            ir_entity_type="function",
            rule_id="test_rule",
            rule_version="1.0.0"
        )
        
        prov_dict = prov.to_dict()
        
        assert "ir_entity" in prov_dict
        assert "rule" in prov_dict
        assert prov_dict["ir_entity"]["id"] == "test"


# ============================================================================
# TEST SYNTHESIS RESULT
# ============================================================================


class TestSynthesisResult:
    """Test synthesis result container."""

    def test_result_creation(self):
        result = SynthesisResult(success=True, contract=None)
        
        assert result.success is True
        assert result.clauses_generated == 0

    def test_add_warning(self):
        result = SynthesisResult(success=True, contract=None)
        
        result.add_warning("Test warning")
        
        assert len(result.warnings) == 1
        assert "Test warning" in result.warnings[0]

    def test_add_error(self):
        result = SynthesisResult(success=True, contract=None)
        
        result.add_error("Test error")
        
        assert len(result.errors) == 1

    def test_record_clause_provenance(self):
        result = SynthesisResult(success=True, contract=None)
        
        prov = ClauseProvenance(
            ir_entity_id="test",
            ir_entity_type="type",
            rule_id="rule",
            rule_version="1.0.0"
        )
        
        result.record_clause("clause_123", prov)
        
        assert "clause_123" in result.provenance_map


# ============================================================================
# TEST LAYOUT CLAUSE GENERATOR
# ============================================================================


class TestLayoutClauseGenerator:
    """Test layout clause generation."""

    @pytest.fixture
    def config(self):
        return SynthesisConfig()

    @pytest.fixture
    def generator(self, config):
        return LayoutClauseGenerator(config)

    def test_generate_structure_layout(self, generator):
        # Create IR structure type
        struct_type = StructureType(
            size_bytes=8,
            alignment_bytes=4,
            structure_name="Point",
            fields=[
                FieldEntity(field_index=0, field_name="x", type_reference="int", byte_offset=0),
                FieldEntity(field_index=1, field_name="y", type_reference="int", byte_offset=4)
            ]
        )
        
        clause = generator.generate_structure_layout(struct_type)
        
        assert clause is not None
        assert clause.clause_type == ClauseType.LAYOUT
        assert "layout_" in clause.clause_id

    def test_layout_clause_has_provenance(self, generator):
        struct_type = StructureType(
            size_bytes=16,
            alignment_bytes=8,
            structure_name="Test"
        )
        
        clause = generator.generate_structure_layout(struct_type)
        
        assert "provenance" in clause.metadata
        prov = clause.metadata["provenance"]
        assert prov["ir_entity"]["type"] == "structure"

    def test_generate_union_layout(self, generator):
        union_type = UnionType(
            size_bytes=8,
            alignment_bytes=8,
            union_name="Data"
        )
        
        clause = generator.generate_union_layout(union_type)
        
        assert clause is not None
        assert clause.clause_type == ClauseType.LAYOUT

    def test_generate_scalar_constraints(self, generator):
        scalar_type = ScalarType(
            size_bytes=4,
            alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER,
            bit_width=32,
            is_signed=True
        )
        
        clauses = generator.generate_scalar_constraints(scalar_type)
        
        assert len(clauses) == 2
        
        # Verify SizeClause
        size_clause = next((c for c in clauses if c.clause_type == ClauseType.SIZE), None)
        assert size_clause is not None
        assert "provenance" in size_clause.metadata
        
        # Verify AlignmentClause
        align_clause = next((c for c in clauses if c.clause_type == ClauseType.ALIGNMENT), None)
        assert align_clause is not None
        assert "provenance" in align_clause.metadata


# ============================================================================
# TEST NULLABILITY CLAUSE GENERATOR
# ============================================================================


class TestNullabilityClauseGenerator:
    """Test nullability clause generation."""

    @pytest.fixture
    def config(self):
        return SynthesisConfig(default_pointer_nonnull=True)

    @pytest.fixture
    def generator(self, config):
        return NullabilityClauseGenerator(config)

    def test_generate_nonnull_default(self, generator):
        # Create type map
        ptr_type = PointerType(pointer_width=64, pointer_depth=1, target_type_reference="int")
        type_map = {ptr_type.entity_id: ptr_type}
        
        param = ParameterEntity(
            parameter_index=0,
            parameter_name="buffer",
            type_reference=ptr_type.entity_id
        )
        
        function = FunctionSymbol(
            linkage_name="process",
            source_name="process",
            calling_convention=CallingConvention.CDECL
        )
        
        clause = generator.generate_parameter_nullability(function, param, type_map)
        
        assert clause is not None
        assert clause.clause_type == ClauseType.NULLABILITY

    def test_nullable_signal_detection(self, generator):
        # Parameter with "optional" in name
        param = ParameterEntity(
            parameter_index=0,
            parameter_name="optional_buffer",
            type_reference="ptr"
        )
        
        has_signal = generator._has_nullable_signals(param)
        
        assert has_signal is True


# ============================================================================
# TEST OWNERSHIP CLAUSE GENERATOR
# ============================================================================


class TestOwnershipClauseGenerator:
    """Test ownership clause generation."""

    @pytest.fixture
    def config(self):
        return SynthesisConfig(default_return_ownership="caller")

    @pytest.fixture
    def generator(self, config):
        return OwnershipClauseGenerator(config)

    def test_generate_return_ownership(self, generator):
        # Setup types
        ptr_type = PointerType(pointer_width=64, pointer_depth=1, target_type_reference="void")
        type_map = {ptr_type.entity_id: ptr_type}
        
        function = FunctionSymbol(
            linkage_name="allocate",
            source_name="allocate",
            calling_convention=CallingConvention.CDECL,
            return_entity=ReturnEntity(type_reference=ptr_type.entity_id)
        )
        
        clause = generator.generate_return_ownership(function, type_map)
        
        assert clause is not None
        assert clause.clause_type == ClauseType.OWNERSHIP


# ============================================================================
# TEST MAIN SYNTHESIS ENGINE
# ============================================================================


class TestSynthesisEngine:
    """Test main synthesis engine orchestration."""

    @pytest.fixture
    def engine(self):
        config = SynthesisConfig()
        return SynthesisEngine(config)

    @pytest.fixture
    def sample_ir(self):
        # Create sample IR with structure and function
        struct_type = StructureType(
            size_bytes=8,
            alignment_bytes=4,
            structure_name="Point",
            fields=[
                FieldEntity(field_index=0, field_name="x", type_reference="int", byte_offset=0),
                FieldEntity(field_index=1, field_name="y", type_reference="int", byte_offset=4)
            ]
        )
        
        ptr_type = PointerType(
            pointer_width=64, 
            pointer_depth=1, 
            target_type_reference=struct_type.entity_id
        )
        
        param = ParameterEntity(
            parameter_index=0,
            parameter_name="point_ptr",
            type_reference=ptr_type.entity_id
        )
        
        function = FunctionSymbol(
            linkage_name="process_point",
            source_name="process_point",
            calling_convention=CallingConvention.CDECL,
            parameters=[param]
        )
        
        ir_unit = InterfaceUnit(
            target_architecture="x86_64",
            operating_system="linux",
            pointer_width=64,
            endianness=Endianness.LITTLE,
            abi_mode="sysv",
            compiler_family="gcc",
            compiler_version="11.2.0"
        )
        
        ir_unit.types.append(struct_type)
        
        # Add scalar type
        scalar_type = ScalarType(
            size_bytes=4,
            alignment_bytes=4,
            scalar_kind=ScalarKind.SIGNED_INTEGER,
            bit_width=32,
            is_signed=True
        )
        ir_unit.types.append(scalar_type)
        
        ir_unit.types.append(ptr_type)
        ir_unit.symbols.append(function)
        
        return ir_unit

    def test_engine_initialization(self, engine):
        assert engine.config is not None
        assert engine.layout_generator is not None
        assert engine.nullability_generator is not None

    def test_synthesize_basic(self, engine, sample_ir):
        result = engine.synthesize(sample_ir, "test_interface")
        
        assert result.success is True
        assert result.contract is not None
        assert result.clauses_generated > 0

    def test_synthesize_generates_layout_clauses(self, engine, sample_ir):
        result = engine.synthesize(sample_ir, "test_interface")
        
        assert result.layout_clauses > 0
        
        # Verify specific structure layout
        clauses = result.contract.get_clauses_by_type(ClauseType.LAYOUT)
        assert len(clauses) >= 1

    def test_synthesize_generates_nullability_clauses(self, engine, sample_ir):
        result = engine.synthesize(sample_ir, "test_interface")
        
        assert result.nullability_clauses > 0

    def test_synthesize_records_provenance(self, engine, sample_ir):
        result = engine.synthesize(sample_ir, "test_interface")
        
        assert len(result.provenance_map) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
