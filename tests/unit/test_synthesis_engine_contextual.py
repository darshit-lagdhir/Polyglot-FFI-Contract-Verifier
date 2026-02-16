
import pytest
from typing import List, Dict, Any, Optional

# Import normalized IR
from module_05_ir_normalization.ir_entities import (
    InterfaceUnit, FunctionSymbol, ParameterEntity, TypeEntity,
    ScalarType, PointerType, ScalarKind, EntityKind, CallingConvention,
    Endianness, FieldEntity
)

# Import contract schema
from module_06_contract_schema.contract_entities import (
    ContractDocument, ContractClause, ClauseType, Severity, SubjectKind, SubjectReference,
    ConstraintParameter
)

# Import synthesis engine components
from module_07_contract_synthesis.synthesis_engine import (
    SynthesisConfig, SynthesisEngine, ContextualAnalyzer, 
    InterfacePattern, ConditionalNullabilityClauseGenerator, 
    SeverityEscalator, AdvisoryClauseGenerator, ConditionalConstraint,
    SynthesisResult
)

@pytest.fixture
def config():
    return SynthesisConfig()

@pytest.fixture
def analyzer(config):
    return ContextualAnalyzer(config)

@pytest.fixture
def conditional_generator(config):
    return ConditionalNullabilityClauseGenerator(config)

@pytest.fixture
def escalator(config):
    return SeverityEscalator(config)

@pytest.fixture
def advisory_generator(config):
    return AdvisoryClauseGenerator(config)

class TestContextualAnalyzer:
    """Test interface-wide contextual analysis."""

    def test_detect_repeated_buffer_length_pattern(self, analyzer):
        # Create 3 functions with buffer-length pattern
        functions = []
        type_map = {}
        
        # Types
        void_ptr = PointerType(pointer_width=64, pointer_depth=1)
        void_ptr.entity_id = "void*"
        type_map["void*"] = void_ptr
        
        size_t = ScalarType(size_bytes=8)
        size_t.scalar_kind = ScalarKind.UNSIGNED_INTEGER
        size_t.entity_id = "size_t"
        type_map["size_t"] = size_t

        for i in range(3):
            buffer_param = ParameterEntity(
                parameter_index=0,
                parameter_name="buffer",
                type_reference="void*"
            )
            size_param = ParameterEntity(
                parameter_index=1,
                parameter_name="length",
                type_reference="size_t"
            )
            
            func = FunctionSymbol(
                linkage_name=f"process_{i}",
                source_name=f"process_{i}",
                calling_convention=CallingConvention.CDECL
            )
            func.entity_id = f"process_{i}"
            func.parameters = [buffer_param, size_param]
            functions.append(func)
            
        ir_unit = InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", pointer_width=64, 
            abi_mode="sysv", endianness=Endianness.LITTLE,
            compiler_family="gcc", compiler_version="11"
        )
        ir_unit.symbols = functions
        ir_unit.types = [void_ptr, size_t]
        
        analysis = analyzer.analyze_interface(ir_unit)
        
        assert len(analysis["patterns"]) > 0
        pattern = analysis["patterns"][0]
        assert pattern.pattern_type == "buffer_length"
        assert pattern.occurrences == 3
        assert pattern.pattern_strength > 0.6

    def test_detect_ownership_symmetry(self, analyzer):
        functions = []
        type_map = {}
        
        void_ptr = PointerType(pointer_width=64, pointer_depth=1)
        void_ptr.target_type_reference = "MyStruct"
        void_ptr.entity_id = "MyStruct*"
        type_map["MyStruct*"] = void_ptr
        
        # Creator
        alloc_func = FunctionSymbol(linkage_name="create_struct", source_name="create_struct", calling_convention=CallingConvention.CDECL)
        alloc_func.entity_id = "create_struct"
        ret_ent = ParameterEntity(parameter_index=-1, parameter_name="ret", type_reference="MyStruct*") 
        alloc_func.return_entity = FieldEntity(
            field_index=-1, field_name="ret", type_reference="MyStruct*", byte_offset=0
        )
        
        # Destroyer
        free_func = FunctionSymbol(linkage_name="destroy_struct", source_name="destroy_struct", calling_convention=CallingConvention.CDECL)
        free_func.entity_id = "destroy_struct"
        p1 = ParameterEntity(parameter_index=0, parameter_name="ptr", type_reference="MyStruct*")
        free_func.parameters = [p1]
        
        functions = [alloc_func, free_func]
        ir_unit = InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", pointer_width=64, 
            abi_mode="sysv", endianness=Endianness.LITTLE,
            compiler_family="gcc", compiler_version="11"
        )
        ir_unit.symbols = functions
        ir_unit.types = [void_ptr]
        
        analysis = analyzer.analyze_interface(ir_unit)
        
        assert len(analysis["ownership_pairs"]) == 1
        pair = analysis["ownership_pairs"][0]
        assert "create" in pair[0]
        assert "destroy" in pair[1]

class TestConditionalNullabilityGenerator:
    def test_generate_conditional_clause(self, conditional_generator):
        buffer_param = ParameterEntity(parameter_name="buffer", parameter_index=0, type_reference="void*")
        size_param = ParameterEntity(parameter_name="length", parameter_index=1, type_reference="size_t")
        
        function = FunctionSymbol(linkage_name="process", source_name="process", calling_convention=CallingConvention.CDECL)
        function.entity_id = "process"
        
        clause = conditional_generator.generate_conditional_nullability(
            function, buffer_param, size_param
        )
        
        assert clause is not None
        assert clause.clause_type == ClauseType.NULLABILITY
        assert "conditional_constraint" in clause.metadata
        cond = clause.metadata["conditional_constraint"]
        assert cond["parameter"] == "length"
        assert cond["operator"] == ">"

class TestSeverityEscalator:
    def test_escalate_relational_clause(self, escalator):
        subject = SubjectReference(subject_kind=SubjectKind.PARAMETER, entity_id="func::buffer")
        clause = ContractClause(
            clause_id="rel_test",
            clause_type=ClauseType.RELATIONAL,
            subject_reference=subject,
            constraint_parameters=[],
            severity=Severity.WARNING
        )
        
        analysis = {
            "patterns": [
                InterfacePattern(
                    pattern_type="buffer_length",
                    occurrences=9,
                    total_functions=10,
                    consistency_score=0.9,
                    example_functions=[]
                )
            ]
        }
        
        escalated = escalator.escalate_clauses([clause], analysis)
        assert escalated[0].severity == Severity.ERROR
        assert escalated[0].metadata.get("escalated") is True

class TestAdvisoryClauseGenerator:
    def test_generate_anomaly_advisory(self, advisory_generator):
        anomaly = {
            "type": "missing_pattern",
            "function": "outlier_func",
            "message": "Deviates from pattern"
        }
        
        clause = advisory_generator.generate_anomaly_advisory(anomaly)
        
        assert clause.clause_type == ClauseType.ADVISORY
        assert clause.severity == Severity.INFO
        assert "outlier_func" in clause.subject_reference.entity_id

class TestSynthesisEngineContextual:
    @pytest.fixture
    def engine(self):
        return SynthesisEngine(SynthesisConfig())
        
    def test_synthesis_full_contextual(self, engine):
        # Create rich interface
        functions = []
        types = []
        
        void_ptr = PointerType(pointer_width=64, pointer_depth=1)
        void_ptr.entity_id = "void*"
        types.append(void_ptr)
        
        size_t = ScalarType(size_bytes=8)
        size_t.scalar_kind = ScalarKind.UNSIGNED_INTEGER
        size_t.entity_id = "size_t"
        types.append(size_t)
        
        for i in range(5):
            f = FunctionSymbol(linkage_name=f"f{i}", source_name=f"f{i}", calling_convention=CallingConvention.CDECL)
            f.entity_id = f"f{i}"
            f.parameters = [
                ParameterEntity(parameter_name="buffer", parameter_index=0, type_reference="void*"),
                ParameterEntity(parameter_name="len", parameter_index=1, type_reference="size_t")
            ]
            functions.append(f)
            
        ir_unit = InterfaceUnit(
            target_architecture="x86_64", operating_system="linux", pointer_width=64, 
            abi_mode="sysv", endianness=Endianness.LITTLE,
            compiler_family="gcc", compiler_version="11"
        )
        ir_unit.symbols = functions
        ir_unit.types = types
        ir_unit.entity_id = "pattern_lib"
        
        result = engine.synthesize(ir_unit, "target")
        
        assert result.success
        assert "contextual_analysis" in result.metadata
        
        # Check conditional clauses generated
        # engine logs explicit count but hard to verify log without capture
        # Try to find conditional clause in contract
        found_cond = False
        for c in result.contract.clauses:
            if "conditional_constraint" in c.metadata:
                found_cond = True
                break
        assert found_cond
        
        # Check escalation (base confidence for buffer/len is ~0.7->Warning?)
        # With 5 functions, pattern strength should propagate
        # Though escalation rules for Relational need pattern strength >= 0.7
        # 5/5 = 1.0 strength.
        # So it should escalate to ERROR if base was WARNING.
        # Base logic: confidence >= 0.8 -> ERROR, >= 0.6 -> WARNING
        # Detector confidence:
        # "buffer" + "len" match -> 0.4 (names)
        # Adjacency -> 0.3
        # Unsigned -> 0.2
        # Order -> 0.1
        # Total = 1.0 -> Starts as ERROR already.
        # So escalation logic from Warning -> Error might not trigger if it's ALREADY Error.
        # But escalation logic stays valid.
