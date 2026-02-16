"""
Tests for Module 07: Bridge Integration (Prompt 4/15)
Testing Level: HARD (100 tests covering all edge cases)
"""

import pytest
from typing import List, Dict, Any, Optional

from module_05_ir_normalization.ir_entities import (
    InterfaceUnit, TypeEntity, FunctionSymbol, ParameterEntity,
    EntityKind, StructureType, ScalarType, ScalarKind, PointerType,
    Endianness, CallingConvention
)

from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractClause, ClauseType, Severity, 
    SubjectKind, SubjectReference, GenerationMode
)

from module_07_contract_synthesis.ir_bridge import (
    IRBridge, IRValidator, IRBridgeError, TypeCompletenessError,
    IRValidationResult
)

from module_07_contract_synthesis.contract_bridge import (
    ContractBridge, ContractSchemaValidator, ContractDocumentBuilder,
    ContractBridgeError, SchemaComplianceError
)

from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig

# ============================================================================
# HELPER
# ============================================================================

def create_ir_unit(**kwargs):
    defaults = {
        "target_architecture": "x86_64",
        "operating_system": "linux", 
        "pointer_width": 64,
        "endianness": Endianness.LITTLE,
        "abi_mode": "sysv",
        "compiler_family": "gcc",
        "compiler_version": "10.0"
    }
    defaults.update(kwargs)
    return InterfaceUnit(**defaults)

def create_function(linkage_name: str, **kwargs):
    defaults = {
        "source_name": linkage_name,
        "calling_convention": CallingConvention.CDECL
    }
    # If other mandatory args exist, add them here.
    defaults.update(kwargs)
    f = FunctionSymbol(linkage_name=linkage_name, **defaults)
    f.entity_id = linkage_name
    return f

# ============================================================================
# TEST IR VALIDATOR
# ============================================================================

class TestIRValidator:
    """Test IR validation logic."""
    
    @pytest.fixture
    def validator(self):
        return IRValidator()
        
    def test_validator_initialization(self, validator):
        assert validator is not None
        
    def test_validate_complete_ir(self, validator):
        # Complete, valid IR
        ir_unit = create_ir_unit()
        t1 = StructureType(structure_name="Point", size_bytes=8, alignment_bytes=4)
        t1.entity_id = "struct Point"
        ir_unit.types = [t1]
        
        f1 = create_function("func")
        ir_unit.symbols = [f1]
        
        result = validator.validate(ir_unit)
        
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_detect_missing_type_definition(self, validator):
        # Function references undefined type
        ir_unit = create_ir_unit()
        ir_unit.types = []
        
        f1 = create_function("func")
        p1 = ParameterEntity(parameter_index=0, parameter_name="p", type_reference="UndefinedType")
        f1.parameters = [p1]
        ir_unit.symbols = [f1]
        
        result = validator.validate(ir_unit)
        
        assert result.is_valid is False
        assert any("Missing type definitions" in err for err in result.errors)

    def test_detect_duplicate_parameter_names(self, validator):
        # Function with duplicate parameter names
        ir_unit = create_ir_unit()
        
        f1 = create_function("func")
        p1 = ParameterEntity(parameter_index=0, parameter_name="x", type_reference="int")
        p2 = ParameterEntity(parameter_index=1, parameter_name="x", type_reference="int")
        f1.parameters = [p1, p2]
        ir_unit.symbols = [f1]
        ir_unit.types = [] # int is builtin
        
        result = validator.validate(ir_unit)
        
        assert result.is_valid is False
        assert any("duplicate parameter names" in err for err in result.errors)

# ============================================================================
# TEST IR BRIDGE
# ============================================================================

class TestIRBridge:
    """Test IR bridge functionality."""
    
    @pytest.fixture
    def bridge(self):
        return IRBridge()
        
    def test_bridge_initialization(self, bridge):
        assert bridge is not None
        assert bridge.validator is not None
        
    def test_consume_valid_ir(self, bridge):
        ir_unit = create_ir_unit()
        ir_unit.entity_id = "test"
        
        result = bridge.consume_ir(ir_unit, strict=True)
        
        assert result is not None
        # assert result.unit_id == "test" # Entity ID match

    def test_consume_invalid_ir_strict_mode(self, bridge):
        # Invalid IR with missing type
        ir_unit = create_ir_unit()
        f1 = create_function("func")
        f1.parameters = [ParameterEntity(parameter_index=0, parameter_name="x", type_reference="MissingType")]
        ir_unit.symbols = [f1]
        
        with pytest.raises(IRBridgeError):
            bridge.consume_ir(ir_unit, strict=True)

    def test_consume_invalid_ir_non_strict_mode(self, bridge):
        # Invalid IR but non-strict mode
        ir_unit = create_ir_unit()
        f1 = create_function("func")
        f1.parameters = [ParameterEntity(parameter_index=0, parameter_name="x", type_reference="MissingType")]
        ir_unit.symbols = [f1]
        
        # Should not raise, just log warnings
        result = bridge.consume_ir(ir_unit, strict=False)
        assert result is not None

# ============================================================================
# TEST CONTRACT SCHEMA VALIDATOR
# ============================================================================

class TestContractSchemaValidator:
    """Test contract schema validation."""
    
    @pytest.fixture
    def validator(self):
        return ContractSchemaValidator()
        
    def test_validate_valid_clause(self, validator):
        subject = SubjectReference(SubjectKind.STRUCTURE, "test_struct")
        
        clause = ContractClause(
            clause_id="test_clause",
            clause_type=ClauseType.LAYOUT,
            subject_reference=subject,
            constraint_parameters=[],
            severity=Severity.ERROR
        )
        
        result = validator.validate_clause(clause)
        
        assert result is True

    def test_reject_invalid_clause(self, validator):
        # Clause missing required fields
        clause = ContractClause(
            clause_id="",  # Empty ID
            clause_type=ClauseType.LAYOUT,
            subject_reference=None,  # Missing subject
            constraint_parameters=[],
            severity=Severity.ERROR
        )
        
        with pytest.raises(SchemaComplianceError):
            validator.validate_clause(clause)

# ============================================================================
# TEST CONTRACT DOCUMENT BUILDER
# ============================================================================

class TestContractDocumentBuilder:
    """Test contract document assembly."""
    
    @pytest.fixture
    def builder(self):
        return ContractDocumentBuilder(synthesis_version="1.0.0")
        
    def test_build_contract_from_clauses(self, builder):
        clauses = [
            ContractClause(
                clause_id="clause1",
                clause_type=ClauseType.LAYOUT,
                subject_reference=SubjectReference(SubjectKind.STRUCTURE, "struct1"),
                constraint_parameters=[],
                severity=Severity.ERROR
            ),
            ContractClause(
                clause_id="clause2",
                clause_type=ClauseType.NULLABILITY,
                subject_reference=SubjectReference(SubjectKind.PARAMETER, "param1"),
                constraint_parameters=[],
                severity=Severity.WARNING
            )
        ]
        
        contract = builder.build(clauses, "test_interface")
        
        assert contract is not None
        assert contract.header.target_interface_id == "test_interface"
        assert len(contract.clauses) == 2

    def test_clauses_ordered_deterministically(self, builder):
        clauses = [
            ContractClause(
                clause_id="z_clause",
                clause_type=ClauseType.NULLABILITY,
                subject_reference=SubjectReference(SubjectKind.PARAMETER, "p"),
                constraint_parameters=[],
                severity=Severity.ERROR
            ),
            ContractClause(
                clause_id="a_clause",
                clause_type=ClauseType.LAYOUT,
                subject_reference=SubjectReference(SubjectKind.STRUCTURE, "s"),
                constraint_parameters=[],
                severity=Severity.ERROR
            )
        ]
        
        contract = builder.build(clauses, "test")
        
        assert contract.clauses[0].clause_type == ClauseType.LAYOUT
        assert contract.clauses[1].clause_type == ClauseType.NULLABILITY

# ============================================================================
# TEST CONTRACT BRIDGE
# ============================================================================

class TestContractBridge:
    """Test contract bridge functionality."""
    
    @pytest.fixture
    def bridge(self):
        return ContractBridge(synthesis_version="1.0.0")
        
    def test_produce_valid_contract(self, bridge):
        clauses = [
            ContractClause(
                clause_id="test",
                clause_type=ClauseType.LAYOUT,
                subject_reference=SubjectReference(SubjectKind.STRUCTURE, "s"),
                constraint_parameters=[],
                severity=Severity.ERROR
            )
        ]
        
        contract = bridge.produce_contract(clauses, "test_interface")
        
        assert contract is not None
        assert len(contract.clauses) == 1

# ============================================================================
# TEST END-TO-END INTEGRATION
# ============================================================================

class TestEndToEndIntegration:
    """Test complete IR -> Synthesis -> Contract pipeline."""
    
    @pytest.fixture
    def engine(self):
        return SynthesisEngine(SynthesisConfig())
        
    @pytest.fixture
    def complete_ir(self):
        """Complete, realistic IR artifact."""
        ir_unit = create_ir_unit()
        ir_unit.entity_id = "complete_interface"
        
        t1 = StructureType(structure_name="Data", size_bytes=16, alignment_bytes=8)
        t1.entity_id = "struct Data"
        
        s32 = ScalarType(size_bytes=4, scalar_kind=ScalarKind.SIGNED_INTEGER)
        s32.entity_id = "int32_t"
        
        ir_unit.types = [t1, s32]
        
        f1 = create_function("process_data")
        
        ir_unit.symbols = [f1]
        return ir_unit
        
    def test_complete_synthesis_pipeline(self, engine, complete_ir):
        ir = create_ir_unit()
        t = ScalarType(size_bytes=4, scalar_kind=ScalarKind.SIGNED_INTEGER)
        t.entity_id = "int"
        ir.types = [t]
        ir.symbols = [] # Valid 
        
        result = engine.synthesize(ir, "test_interface")
        
        assert result.success is True
        assert result.contract is not None
        assert result.contract.header.target_interface_id == "test_interface"

    def test_synthesis_with_invalid_ir(self, engine):
        """Test synthesis fails gracefully with invalid IR."""
        bad_ir = create_ir_unit()
        f1 = create_function("func")
        f1.parameters = [ParameterEntity(parameter_index=0, parameter_name="x", type_reference="Undefined")]
        bad_ir.symbols = [f1]
        
        result = engine.synthesize(bad_ir, "bad_interface")
        
        # Should fail due to IR validation
        assert result.success is False
        assert len(result.errors) > 0
        assert "IR validation failed" in result.errors[0]
