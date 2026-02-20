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
# File Integrity Identifier: 6b4703d57d7085a1
# ==============================================================================

@dataclass
class ValidationReport:
    """Comprehensive validation report."""

    passed: bool = True

    schema_errors: List[str] = field(default_factory=list)
    reference_errors: List[str] = field(default_factory=list)
    type_errors: List[str] = field(default_factory=list)
    symbol_errors: List[str] = field(default_factory=list)
    graph_errors: List[str] = field(default_factory=list)
    platform_errors: List[str] = field(default_factory=list)
    completeness_errors: List[str] = field(default_factory=list)

    def total_errors(self) -> int:
        """Get total error count."""
        return (
            len(self.schema_errors)
            + len(self.reference_errors)
            + len(self.type_errors)
            + len(self.symbol_errors)
            + len(self.graph_errors)
            + len(self.platform_errors)
            + len(self.completeness_errors)
        )

    def all_errors(self) -> List[str]:
        """Get all errors concatenated."""
        return (
            self.schema_errors
            + self.reference_errors
            + self.type_errors
            + self.symbol_errors
            + self.graph_errors
            + self.platform_errors
            + self.completeness_errors
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize report."""
        return {
            "passed": self.passed,
            "total_errors": self.total_errors(),
            "schema_errors": self.schema_errors,
            "reference_errors": self.reference_errors,
            "type_errors": self.type_errors,
            "symbol_errors": self.symbol_errors,
            "graph_errors": self.graph_errors,
            "platform_errors": self.platform_errors,
            "completeness_errors": self.completeness_errors,
        }


# ============================================================================
# SCHEMA VALIDATOR
# ============================================================================


class SchemaValidator:
    """Validates IR entities conform to schema."""

    def validate_entity(self, entity: IREntity) -> List[str]:
        errors = []

        # All entities must have ID and kind
        if not entity.entity_id:
            errors.append("Entity missing entity_id")

        if not entity.kind:
            errors.append("Entity missing kind")

        # Type-specific validation
        if isinstance(entity, TypeEntity):
            errors.extend(self._validate_type_entity(entity))
        elif isinstance(entity, SymbolEntity):
            errors.extend(self._validate_symbol_entity(entity))
        elif isinstance(entity, FieldEntity):
            errors.extend(self._validate_field_entity(entity))

        return errors

    def _validate_type_entity(self, entity: TypeEntity) -> List[str]:
        """Validate type entity schema."""
        errors = []

        if entity.size_bytes < 0:
            errors.append(f"Type {entity.entity_id} has negative size")

        if entity.alignment_bytes <= 0:
            errors.append(f"Type {entity.entity_id} has invalid alignment")

        # Alignment must be power of 2
        if entity.alignment_bytes > 0:
            if (entity.alignment_bytes & (entity.alignment_bytes - 1)) != 0:
                errors.append(
                    f"Type {entity.entity_id} alignment {entity.alignment_bytes} is not power of 2"
                )

        return errors

    def _validate_symbol_entity(self, entity: SymbolEntity) -> List[str]:
        """Validate symbol entity schema."""
        errors = []

        if not entity.linkage_name:
            errors.append(f"Symbol {entity.entity_id} missing linkage_name")

        return errors

    def _validate_field_entity(self, entity: FieldEntity) -> List[str]:
        """Validate field entity schema."""
        errors = []
        if entity.field_index < 0:
            errors.append(f"Field {entity.entity_id} has negative index")
        if entity.byte_offset < 0:
            errors.append(f"Field {entity.entity_id} has negative offset")
        return errors


# ============================================================================
# REFERENCE VALIDATOR
# ============================================================================


class ReferenceValidator:
    """Validates all entity references resolve."""

    def __init__(self, type_registry: TypeRegistry) -> None:
        self.type_registry = type_registry

    def validate_all_references(self, entities: Sequence[IREntity]) -> List[str]:
        """Validate all entity references."""
        errors = []

        for entity in entities:
            if isinstance(entity, PointerType):
                errors.extend(self._validate_pointer_references(entity))
            elif isinstance(entity, ArrayType):
                errors.extend(self._validate_array_references(entity))
            elif isinstance(entity, StructureType):
                errors.extend(self._validate_structure_references(entity))
            elif isinstance(entity, UnionType):
                errors.extend(self._validate_union_references(entity))
            elif isinstance(entity, EnumerationType):
                errors.extend(self._validate_enum_references(entity))
            elif isinstance(entity, FunctionPointerType):
                errors.extend(self._validate_function_pointer_references(entity))
            elif isinstance(entity, FunctionSymbol):
                errors.extend(self._validate_function_references(entity))

        return errors

    def _validate_pointer_references(self, ptr: PointerType) -> List[str]:
        """Validate pointer type references."""
        errors = []
        target = self.type_registry.resolve_type(ptr.target_type_reference)
        if not target:
            errors.append(
                f"Pointer {ptr.entity_id} references undefined target type {ptr.target_type_reference}"
            )
        return errors

    def _validate_array_references(self, array: ArrayType) -> List[str]:
        """Validate array type references."""
        errors = []
        element = self.type_registry.resolve_type(array.element_type_reference)
        if not element:
            errors.append(
                f"Array {array.entity_id} references undefined element type {array.element_type_reference}"
            )
        return errors

    def _validate_structure_references(self, struct: StructureType) -> List[str]:
        """Validate structure field references."""
        errors = []
        for field in struct.fields:
            field_type = self.type_registry.resolve_type(field.type_reference)
            if not field_type:
                errors.append(
                    f"Structure {struct.structure_name} field {field.field_name} references undefined type {
                        field.type_reference
                    }"
                )
        return errors

    def _validate_union_references(self, union: UnionType) -> List[str]:
        """Validate union member references."""
        errors = []
        for member in union.members:
            member_type = self.type_registry.resolve_type(member.type_reference)
            if not member_type:
                errors.append(
                    f"Union {union.union_name} member {member.field_name} references undefined type {
                        member.type_reference
                    }"
                )
        return errors

    def _validate_enum_references(self, enum: EnumerationType) -> List[str]:
        """Validate enum underlying type reference."""
        errors = []
        underlying = self.type_registry.resolve_type(enum.underlying_type_reference)
        if not underlying:
            errors.append(
                f"Enum {enum.enum_name} references undefined underlying type {enum.underlying_type_reference}"
            )
        return errors

    def _validate_function_pointer_references(self, fp: FunctionPointerType) -> List[str]:
        """Validate function pointer references."""
        errors = []
        ret = self.type_registry.resolve_type(fp.return_type_reference)
        if not ret:
            errors.append(
                f"FunctionPointer references undefined return type {fp.return_type_reference}"
            )
        for param in fp.parameters:
            pt = self.type_registry.resolve_type(param.type_reference)
            if not pt:
                errors.append(
                    f"FunctionPointer parameter references undefined type {param.type_reference}"
                )
        return errors

    def _validate_function_references(self, func: FunctionSymbol) -> List[str]:
        """Validate function symbol references."""
        errors = []
        if func.return_entity:
            return_type = self.type_registry.resolve_type(func.return_entity.type_reference)
            if not return_type:
                errors.append(
                    f"Function {func.linkage_name} references undefined return type {func.return_entity.type_reference}"
                )
        for param in func.parameters:
            param_type = self.type_registry.resolve_type(param.type_reference)
            if not param_type:
                errors.append(
                    f"Function {func.linkage_name} parameter {param.parameter_name} references undefined type {
                        param.type_reference
                    }"
                )
        return errors


# ============================================================================
# TYPE VALIDATOR
# ============================================================================


class TypeValidator:
    """Validates type entities satisfy ABI rules."""

    def validate_structure_layout(self, struct: StructureType) -> List[str]:
        """Validate structure layout consistency."""
        errors: List[str] = []
        if not struct.fields:
            return errors

        sorted_fields = sorted(struct.fields, key=lambda f: f.byte_offset)

        # Check for overlaps
        for i in range(len(sorted_fields) - 1):
            current = sorted_fields[i]
            next_f = sorted_fields[i + 1]
            current_end = current.byte_offset + current.size_bytes
            if next_f.byte_offset < current_end:
                errors.append(
                    f"Structure {struct.structure_name}: field {next_f.field_name} overlaps with {current.field_name}"
                )

        # Check field alignment
        for f in struct.fields:
            if f.alignment_bytes > 0 and f.byte_offset % f.alignment_bytes != 0:
                errors.append(
                    f"Structure {struct.structure_name}: field {f.field_name} violates alignment {f.alignment_bytes}"
                )

        # Check total size
        if sorted_fields:
            last_field = sorted_fields[-1]
            min_size = last_field.byte_offset + last_field.size_bytes
            if struct.size_bytes < min_size:
                errors.append(f"Structure {struct.structure_name} size too small, min {min_size}")

        # Check structure alignment
        if struct.size_bytes % struct.alignment_bytes != 0:
            errors.append(f"Structure {struct.structure_name} size not multiple of alignment")

        return errors

    def validate_union_invariants(self, union: UnionType) -> List[str]:
        """Validate union invariants."""
        errors: List[str] = []
        if not union.members:
            return errors

        # Check all members at offset 0
        for member in union.members:
            if member.byte_offset != 0:
                errors.append(
                    f"Union {union.union_name} member {member.field_name} not at offset 0"
                )

        # Check size is at least max member size
        max_member_size = max(m.size_bytes for m in union.members)
        if union.size_bytes < max_member_size:
            errors.append(
                f"Union {union.union_name} size {union.size_bytes} less than max member size {max_member_size}"
            )

        # Check alignment is at least max member alignment
        max_member_align = max(m.alignment_bytes for m in union.members)
        if union.alignment_bytes < max_member_align:
            errors.append(
                f"Union {union.union_name} alignment {union.alignment_bytes} less than max member alignment {
                    max_member_align
                }"
            )

        return errors

    def validate_array_consistency(self, array: ArrayType) -> List[str]:
        """Validate array size consistency."""
        errors = []
        if array.array_kind == ArrayKind.FIXED_SIZE:
            if array.element_count is None or array.element_count <= 0:
                errors.append(f"Fixed-size array {array.entity_id} invalid element count")
            # elif array.size_bytes != array.element_count * array.element_size:
            #     pass
        return errors

    def validate_enum_ranges(self, enum: EnumerationType, reg: TypeRegistry) -> List[str]:
        """Validate enumerator values fit in underlying type."""
        errors: List[str] = []
        underlying = reg.resolve_type(enum.underlying_type_reference)
        if not isinstance(underlying, ScalarType):
            return errors

        if underlying.is_signed:
            min_val = -(2 ** (underlying.bit_width - 1))
            max_val = 2 ** (underlying.bit_width - 1) - 1
        else:
            min_val = 0
            max_val = 2**underlying.bit_width - 1

        for name, value in enum.enumerators.items():
            if not (min_val <= value <= max_val):
                errors.append(
                    f"Enum {enum.enum_name} value {name}={value} out of range for {underlying.bit_width}-bit type"
                )
        return errors


# ============================================================================
# SYMBOL VALIDATOR
# ============================================================================


class SymbolValidator:
    """Validates symbol entities."""

    def validate_function_symbol(self, func: FunctionSymbol) -> List[str]:
        """Validate function symbol."""
        errors = []

        # Check parameter ordering
        for i, param in enumerate(func.parameters):
            if param.parameter_index != i:
                errors.append(
                    f"Function {func.linkage_name}: parameter index mismatch at position {i}"
                )

        # Check duplicate parameter names
        names = [p.parameter_name for p in func.parameters if p.parameter_name]
        if len(names) != len(set(names)):
            errors.append(f"Function {func.linkage_name} has duplicate parameter names")

        # Check variadic functions
        if func.is_variadic and len(func.parameters) == 0:
            errors.append(f"Variadic function {func.linkage_name} has no named parameters")

        return errors

    def validate_variable_symbol(self, var: VariableSymbol) -> List[str]:
        """Validate variable symbol."""
        errors = []
        if not var.type_reference:
            errors.append(f"Variable {var.linkage_name} missing type reference")
        valid_vis = {"extern", "static", "hidden", "protected", "internal"}
        if var.visibility not in valid_vis:
            errors.append(f"Variable {var.linkage_name} has invalid visibility {var.visibility}")
        return errors


# ============================================================================
# GRAPH VALIDATOR (CYCLES)
# ============================================================================


class GraphValidator:
    """Validates type dependency graph acyclicity."""

    def __init__(self, type_registry: TypeRegistry):
        self.type_registry = type_registry

    def detect_cycles(self) -> List[str]:
        """Detect cycles in type dependency graph."""
        errors = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        for type_entity in self.type_registry.get_all_types():
            if type_entity.entity_id not in visited:
                cycle = self._dfs_detect_cycle(type_entity.entity_id, visited, rec_stack, [])
                if cycle:
                    errors.append(f"Circular type dependency: {' -> '.join(cycle)}")
        return errors

    def _dfs_detect_cycle(
        self, type_id: str, visited: Set[str], rec_stack: Set[str], path: List[str]
    ) -> Optional[List[str]]:
        visited.add(type_id)
        rec_stack.add(type_id)
        path.append(type_id)

        entity = self.type_registry.resolve_type(type_id)
        if entity:
            deps = self._get_dependencies(entity)
            for dep_id in deps:
                if dep_id not in visited:
                    res = self._dfs_detect_cycle(dep_id, visited, rec_stack, path)
                    if res:
                        return res
                elif dep_id in rec_stack:
                    idx = path.index(dep_id)
                    return path[idx:] + [dep_id]

        rec_stack.remove(type_id)
        path.pop()
        return None

    def _get_dependencies(self, entity: TypeEntity) -> List[str]:
        deps = []
        if isinstance(entity, PointerType):
            # Pointers break structural cycles
            pass
        elif isinstance(entity, ArrayType):
            deps.append(entity.element_type_reference)
        elif isinstance(entity, StructureType):
            deps.extend(f.type_reference for f in entity.fields)
        elif isinstance(entity, UnionType):
            deps.extend(m.type_reference for m in entity.members)
        elif isinstance(entity, EnumerationType):
            deps.append(entity.underlying_type_reference)
        return deps


# ============================================================================
# PLATFORM VALIDATOR
# ============================================================================


class PlatformValidator:
    def __init__(self, interface_unit: InterfaceUnit) -> None:
        self.interface_unit = interface_unit

    def validate_pointer_sizes(self, type_registry: TypeRegistry) -> List[str]:
        errors = []
        expected = self.interface_unit.pointer_width // 8
        for t in type_registry.get_all_types():
            if isinstance(t, (PointerType, FunctionPointerType)):
                if t.size_bytes != expected:
                    errors.append(f"Type {t.entity_id} size {t.size_bytes} incompatible with {
                        self.interface_unit.pointer_width
                    }-bit platform")
        return errors

    def validate_calling_conventions(self, symbols: List[SymbolEntity]) -> List[str]:
        errors = []
        arch = self.interface_unit.target_architecture
        for s in symbols:
            if not isinstance(s, FunctionSymbol):
                continue
            if arch == "x86_64" and s.calling_convention in [
                CallingConvention.STDCALL,
                CallingConvention.FASTCALL,
            ]:
                errors.append(
                    f"Function {s.linkage_name} uses {s.calling_convention.value} on x86_64 (unsupported)"
                )
        return errors


# ============================================================================
# COMPLETENESS VALIDATOR
# ============================================================================


class CompletenessValidator:
    """Validates IR completeness."""

    def validate_interface_unit(self, unit: InterfaceUnit) -> List[str]:
        errors = []
        if not unit.target_architecture:
            errors.append("Missing target_architecture")
        if not unit.operating_system:
            errors.append("Missing operating_system")
        if unit.pointer_width not in [32, 64]:
            errors.append(f"Invalid pointer_width {unit.pointer_width}")
        if not unit.symbols:
            errors.append("No symbols in interface")
        if not unit.types:
            errors.append("No types in interface")
        return errors


# ============================================================================
# VALIDATION ORCHESTRATOR
# ============================================================================


class IRValidationOrchestrator:
    """Orchestrates complete IR validation."""

    def __init__(self, interface_unit: InterfaceUnit, type_registry: TypeRegistry) -> None:
        self.interface_unit = interface_unit
        self.type_registry = type_registry

        self.schema_validator = SchemaValidator()
        self.reference_validator = ReferenceValidator(type_registry)
        self.type_validator = TypeValidator()
        self.symbol_validator = SymbolValidator()
        self.graph_validator = GraphValidator(type_registry)
        self.platform_validator = PlatformValidator(interface_unit)
        self.completeness_validator = CompletenessValidator()

    def validate_complete_ir(self) -> ValidationReport:
        """Perform complete IR validation."""
        report = ValidationReport()

        all_entities = self.interface_unit.symbols + self.interface_unit.types

        # : Schema
        for entity in all_entities:
            report.schema_errors.extend(self.schema_validator.validate_entity(entity))

        # : References
        report.reference_errors.extend(
            self.reference_validator.validate_all_references(all_entities)
        )

        # : Types
        for t in self.interface_unit.types:
            if isinstance(t, StructureType):
                report.type_errors.extend(self.type_validator.validate_structure_layout(t))
            elif isinstance(t, UnionType):
                report.type_errors.extend(self.type_validator.validate_union_invariants(t))
            elif isinstance(t, ArrayType):
                report.type_errors.extend(self.type_validator.validate_array_consistency(t))
            elif isinstance(t, EnumerationType):
                report.type_errors.extend(
                    self.type_validator.validate_enum_ranges(t, self.type_registry)
                )

        # : Symbols
        for s in self.interface_unit.symbols:
            if isinstance(s, FunctionSymbol):
                report.symbol_errors.extend(self.symbol_validator.validate_function_symbol(s))
            elif isinstance(s, VariableSymbol):
                report.symbol_errors.extend(self.symbol_validator.validate_variable_symbol(s))

        # : Graph
        report.graph_errors.extend(self.graph_validator.detect_cycles())

        # : Platform
        report.platform_errors.extend(
            self.platform_validator.validate_pointer_sizes(self.type_registry)
        )
        report.platform_errors.extend(
            self.platform_validator.validate_calling_conventions(self.interface_unit.symbols)
        )

        # : Completeness
        report.completeness_errors.extend(
            self.completeness_validator.validate_interface_unit(self.interface_unit)
        )

        # Overall status
        report.passed = report.total_errors() == 0

        return report


__all__ = [
    "ValidationReport",
    "SchemaValidator",
    "ReferenceValidator",
    "TypeValidator",
    "SymbolValidator",
    "GraphValidator",
    "PlatformValidator",
    "CompletenessValidator",
    "IRValidationOrchestrator",
]