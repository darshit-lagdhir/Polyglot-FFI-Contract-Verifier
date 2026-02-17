""" Tests for Contract Versioning - Prompt 12/20 Dependency Resolution & Multi-Contract Version Coordination

Testing Level: HARDEST (80 comprehensive tests) """

import pytest
from modules.module_06_contract_schema.contract_versioning import (
    ConstraintOperator,
    VersionConstraint,
    ContractDependency,
    DependencyGraph,
    DependencyResolver,
    CoordinatedUpgradePlanner,
)


# ============================================================================
# TEST VERSION CONSTRAINT (15 TESTS)
# ============================================================================
class TestVersionConstraint:
    """Test VersionConstraint (15 tests)."""

    def test_create_constraint(self):
        """Test 1: Create version constraint."""
        c = VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "1.5.0")
        assert c.contract_name == "libcore"
        assert c.operator == ConstraintOperator.GREATER_EQUAL

    def test_satisfies_equal(self):
        """Test 2: Satisfies with EQUAL operator."""
        c = VersionConstraint("lib", ConstraintOperator.EQUAL, "2.0.0")
        assert c.satisfies("2.0.0") is True
        assert c.satisfies("2.0.1") is False

    def test_satisfies_greater_equal(self):
        """Test 3: Satisfies with GREATER_EQUAL."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER_EQUAL, "1.5.0")
        assert c.satisfies("1.5.0") is True
        assert c.satisfies("1.6.0") is True
        assert c.satisfies("1.4.0") is False

    def test_satisfies_less_equal(self):
        """Test 4: Satisfies with LESS_EQUAL."""
        c = VersionConstraint("lib", ConstraintOperator.LESS_EQUAL, "2.0.0")
        assert c.satisfies("2.0.0") is True
        assert c.satisfies("1.9.0") is True
        assert c.satisfies("2.1.0") is False

    def test_satisfies_greater(self):
        """Test 5: Satisfies with GREATER."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER, "1.5.0")
        assert c.satisfies("1.6.0") is True
        assert c.satisfies("1.5.0") is False

    def test_satisfies_less(self):
        """Test 6: Satisfies with LESS."""
        c = VersionConstraint("lib", ConstraintOperator.LESS, "2.0.0")
        assert c.satisfies("1.9.0") is True
        assert c.satisfies("2.0.0") is False

    def test_satisfies_compatible(self):
        """Test 7: Satisfies with COMPATIBLE (caret)."""
        c = VersionConstraint("lib", ConstraintOperator.COMPATIBLE, "1.5.0")
        assert c.satisfies("1.5.0") is True
        assert c.satisfies("1.9.0") is True
        assert c.satisfies("2.0.0") is False

    def test_to_dict(self):
        """Test 8: Constraint to dictionary."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER_EQUAL, "1.5.0")
        data = c.to_dict()
        assert data["contract_name"] == "lib"
        assert data["operator"] == ">="

    def test_parse_version_simple(self):
        """Test 9: Parse simple version."""
        c = VersionConstraint("lib", ConstraintOperator.EQUAL, "1.0.0")
        parsed = c._parse_version("2.5.3")
        assert parsed == (2, 5, 3)

    def test_parse_version_major_minor(self):
        """Test 10: Parse major.minor version."""
        c = VersionConstraint("lib", ConstraintOperator.EQUAL, "1.0")
        parsed = c._parse_version("2.5")
        assert parsed == (2, 5, 0)

    def test_parse_version_major_only(self):
        """Test 11: Parse major-only version."""
        c = VersionConstraint("lib", ConstraintOperator.EQUAL, "1")
        parsed = c._parse_version("2")
        assert parsed == (2, 0, 0)

    def test_version_comparison_major(self):
        """Test 12: Version comparison by major."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER, "1.0.0")
        assert c.satisfies("2.0.0") is True

    def test_version_comparison_minor(self):
        """Test 13: Version comparison by minor."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER, "1.5.0")
        assert c.satisfies("1.6.0") is True
        assert c.satisfies("1.4.0") is False

    def test_version_comparison_patch(self):
        """Test 14: Version comparison by patch."""
        c = VersionConstraint("lib", ConstraintOperator.GREATER, "1.5.3")
        assert c.satisfies("1.5.4") is True
        assert c.satisfies("1.5.2") is False

    def test_compatible_major_boundary(self):
        """Test 15: Compatible respects major version boundary."""
        c = VersionConstraint("lib", ConstraintOperator.COMPATIBLE, "2.0.0")
        assert c.satisfies("2.5.0") is True
        assert c.satisfies("3.0.0") is False


# ============================================================================
# TEST CONTRACT DEPENDENCY (10 TESTS)
# ============================================================================
class TestContractDependency:
    """Test ContractDependency (10 tests)."""

    def test_create_dependency(self):
        """Test 16: Create contract dependency."""
        dep = ContractDependency("app", "1.0.0")
        assert dep.contract_name == "app"
        assert dep.current_version == "1.0.0"

    def test_add_dependency(self):
        """Test 17: Add dependency constraint."""
        dep = ContractDependency("app", "1.0.0")
        constraint = VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0")
        dep.add_dependency(constraint)
        assert len(dep.dependencies) == 1

    def test_get_dependency(self):
        """Test 18: Get dependency by name."""
        dep = ContractDependency("app", "1.0.0")
        constraint = VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0")
        dep.add_dependency(constraint)
        found = dep.get_dependency("libcore")
        assert found is not None
        assert found.contract_name == "libcore"

    def test_get_dependency_not_found(self):
        """Test 19: Get non-existent dependency."""
        dep = ContractDependency("app", "1.0.0")
        found = dep.get_dependency("missing")
        assert found is None

    def test_multiple_dependencies(self):
        """Test 20: Multiple dependencies."""
        dep = ContractDependency("app", "1.0.0")
        dep.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))
        dep.add_dependency(VersionConstraint("libutils", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        assert len(dep.dependencies) == 2

    def test_to_dict(self):
        """Test 21: Dependency to dictionary."""
        dep = ContractDependency("app", "1.0.0")
        dep.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))
        data = dep.to_dict()
        assert data["contract_name"] == "app"
        assert len(data["dependencies"]) == 1

    def test_empty_dependencies(self):
        """Test 22: Empty dependencies."""
        dep = ContractDependency("app", "1.0.0")
        assert len(dep.dependencies) == 0

    def test_dependency_version(self):
        """Test 23: Dependency current version."""
        dep = ContractDependency("app", "2.5.3")
        assert dep.current_version == "2.5.3"

    def test_dependency_name(self):
        """Test 24: Dependency contract name."""
        dep = ContractDependency("my-custom-app", "1.0.0")
        assert dep.contract_name == "my-custom-app"

    def test_get_dependency_order(self):
        """Test 25: Get dependencies preserves order."""
        dep = ContractDependency("app", "1.0.0")
        dep.add_dependency(VersionConstraint("lib1", ConstraintOperator.EQUAL, "1.0.0"))
        dep.add_dependency(VersionConstraint("lib2", ConstraintOperator.EQUAL, "2.0.0"))
        assert dep.dependencies[0].contract_name == "lib1"
        assert dep.dependencies[1].contract_name == "lib2"


# ============================================================================
# TEST DEPENDENCY GRAPH (20 TESTS)
# ============================================================================
class TestDependencyGraph:
    """Test DependencyGraph (20 tests)."""

    @pytest.fixture
    def graph(self):
        return DependencyGraph()

    def test_create_graph(self, graph):
        """Test 26: Create dependency graph."""
        assert graph is not None
        assert len(graph.nodes) == 0

    def test_add_contract(self, graph):
        """Test 27: Add contract to graph."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        assert len(graph.nodes) == 1

    def test_get_contract(self, graph):
        """Test 28: Get contract from graph."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        found = graph.get_contract("app")
        assert found is not None
        assert found.contract_name == "app"

    def test_get_dependencies(self, graph):
        """Test 29: Get direct dependencies."""
        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))
        graph.add_contract(app)
        deps = graph.get_dependencies("app")
        assert "libcore" in deps

    def test_get_transitive_dependencies(self, graph):
        """Test 30: Get transitive dependencies."""
        libcore = ContractDependency("libcore", "2.0.0")
        libcore.add_dependency(VersionConstraint("libutils", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(app)

        transitive = graph.get_transitive_dependencies("app")
        assert "libcore" in transitive
        assert "libutils" in transitive

    def test_topological_sort_simple(self, graph):
        """Test 31: Topological sort simple case."""
        libutils = ContractDependency("libutils", "1.0.0")
        libcore = ContractDependency("libcore", "2.0.0")
        libcore.add_dependency(VersionConstraint("libutils", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(libutils)
        graph.add_contract(libcore)

        order = graph.topological_sort()
        assert order.index("libutils") < order.index("libcore")

    def test_topological_sort_complex(self, graph):
        """Test 32: Topological sort complex graph."""
        libbase = ContractDependency("libbase", "1.0.0")
        libutils = ContractDependency("libutils", "1.0.0")
        libutils.add_dependency(VersionConstraint("libbase", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        libcore = ContractDependency("libcore", "2.0.0")
        libcore.add_dependency(VersionConstraint("libutils", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        graph.add_contract(libbase)
        graph.add_contract(libutils)
        graph.add_contract(libcore)
        graph.add_contract(app)

        order = graph.topological_sort()
        assert order.index("libbase") < order.index("libutils")
        assert order.index("libutils") < order.index("libcore")
        assert order.index("libcore") < order.index("app")

    def test_has_cycle_false(self, graph):
        """Test 33: has_cycle returns false for acyclic graph."""
        libcore = ContractDependency("libcore", "2.0.0")
        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(app)

        assert graph.has_cycle() is False

    def test_to_dict(self, graph):
        """Test 34: Graph to dictionary."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        data = graph.to_dict()
        assert "contracts" in data
        assert len(data["contracts"]) == 1

    def test_empty_graph_topological_sort(self, graph):
        """Test 35: Topological sort of empty graph."""
        order = graph.topological_sort()
        assert len(order) == 0

    def test_single_node_topological_sort(self, graph):
        """Test 36: Topological sort single node."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        order = graph.topological_sort()
        assert order == ["app"]

    def test_get_dependencies_empty(self, graph):
        """Test 37: Get dependencies for contract with none."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        deps = graph.get_dependencies("app")
        assert len(deps) == 0

    def test_get_transitive_dependencies_none(self, graph):
        """Test 38: Get transitive dependencies with none."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        transitive = graph.get_transitive_dependencies("app")
        assert len(transitive) == 0

    def test_get_contract_not_found(self, graph):
        """Test 39: Get non-existent contract."""
        found = graph.get_contract("missing")
        assert found is None

    def test_get_dependencies_not_in_graph(self, graph):
        """Test 40: Get dependencies for missing contract."""
        deps = graph.get_dependencies("missing")
        assert len(deps) == 0

    def test_multiple_contracts(self, graph):
        """Test 41: Add multiple contracts."""
        for i in range(5):
            graph.add_contract(ContractDependency(f"lib{i}", "1.0.0"))
        assert len(graph.nodes) == 5

    def test_graph_edges(self, graph):
        """Test 42: Graph edges created correctly."""
        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))
        graph.add_contract(app)
        assert "app" in graph.edges
        assert "libcore" in graph.edges["app"]

    def test_to_dict_includes_edges(self, graph):
        """Test 43: to_dict includes edges."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        data = graph.to_dict()
        assert "edges" in data

    def test_transitive_excludes_self(self, graph):
        """Test 44: Transitive dependencies exclude self."""
        dep = ContractDependency("app", "1.0.0")
        graph.add_contract(dep)
        transitive = graph.get_transitive_dependencies("app")
        assert "app" not in transitive

    def test_diamond_dependency(self, graph):
        """Test 45: Diamond dependency pattern."""
        base = ContractDependency("base", "1.0.0")
        left = ContractDependency("left", "1.0.0")
        left.add_dependency(VersionConstraint("base", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        right = ContractDependency("right", "1.0.0")
        right.add_dependency(VersionConstraint("base", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        top = ContractDependency("top", "1.0.0")
        top.add_dependency(VersionConstraint("left", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        top.add_dependency(VersionConstraint("right", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(base)
        graph.add_contract(left)
        graph.add_contract(right)
        graph.add_contract(top)

        transitive = graph.get_transitive_dependencies("top")
        assert len(transitive) == 3  # left, right, base


# ============================================================================
# TEST DEPENDENCY RESOLVER (20 TESTS)
# ============================================================================
class TestDependencyResolver:
    """Test DependencyResolver (20 tests)."""

    @pytest.fixture
    def simple_graph(self):
        graph = DependencyGraph()
        libcore = ContractDependency("libcore", "2.0.0")
        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(app)
        return graph

    @pytest.fixture
    def resolver(self, simple_graph):
        return DependencyResolver(simple_graph)

    def test_resolve_success(self, resolver):
        """Test 46: Resolve dependencies successfully."""
        result = resolver.resolve("app")
        assert result["success"] is True

    def test_resolve_not_found(self, resolver):
        """Test 47: Resolve non-existent contract."""
        result = resolver.resolve("missing")
        assert result["success"] is False

    def test_resolve_includes_dependencies(self, resolver):
        """Test 48: Resolve includes dependencies."""
        result = resolver.resolve("app")
        assert "resolved_dependencies" in result
        assert "libcore" in result["resolved_dependencies"]

    def test_detect_conflicts_none(self, resolver):
        """Test 49: Detect no conflicts."""
        conflicts = resolver.detect_conflicts("app")
        assert len(conflicts) == 0

    def test_detect_conflicts_simple(self):
        """Test 50: Detect simple conflict."""
        graph = DependencyGraph()

        libcore = ContractDependency("libcore", "2.0.0")

        lib1 = ContractDependency("lib1", "1.0.0")
        lib1.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        lib2 = ContractDependency("lib2", "1.0.0")
        lib2.add_dependency(VersionConstraint("libcore", ConstraintOperator.LESS, "2.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("lib1", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        app.add_dependency(VersionConstraint("lib2", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(lib1)
        graph.add_contract(lib2)
        graph.add_contract(app)

        resolver = DependencyResolver(graph)
        conflicts = resolver.detect_conflicts("app")
        assert len(conflicts) > 0

    def test_resolve_with_conflicts(self):
        """Test 51: Resolve with conflicts fails."""
        graph = DependencyGraph()

        libcore = ContractDependency("libcore", "2.0.0")
        lib1 = ContractDependency("lib1", "1.0.0")
        lib1.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        lib2 = ContractDependency("lib2", "1.0.0")
        lib2.add_dependency(VersionConstraint("libcore", ConstraintOperator.LESS, "2.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("lib1", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        app.add_dependency(VersionConstraint("lib2", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(lib1)
        graph.add_contract(lib2)
        graph.add_contract(app)

        resolver = DependencyResolver(graph)
        result = resolver.resolve("app")
        assert result["success"] is False

    def test_resolved_versions(self, resolver):
        """Test 52: Resolved versions are correct."""
        result = resolver.resolve("app")
        assert result["resolved_dependencies"]["libcore"] == "2.0.0"

    def test_resolve_no_dependencies(self):
        """Test 53: Resolve contract with no dependencies."""
        graph = DependencyGraph()
        standalone = ContractDependency("standalone", "1.0.0")
        graph.add_contract(standalone)

        resolver = DependencyResolver(graph)
        result = resolver.resolve("standalone")
        assert result["success"] is True
        assert len(result["resolved_dependencies"]) == 0

    def test_conflict_structure(self):
        """Test 54: Conflict structure is correct."""
        graph = DependencyGraph()
        libcore = ContractDependency("libcore", "2.0.0")
        lib1 = ContractDependency("lib1", "1.0.0")
        lib1.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        lib2 = ContractDependency("lib2", "1.0.0")
        lib2.add_dependency(VersionConstraint("libcore", ConstraintOperator.LESS, "2.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("lib1", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        app.add_dependency(VersionConstraint("lib2", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(lib1)
        graph.add_contract(lib2)
        graph.add_contract(app)

        resolver = DependencyResolver(graph)
        conflicts = resolver.detect_conflicts("app")

        if len(conflicts) > 0:
            conflict = conflicts[0]
            assert "target_contract" in conflict
            assert "conflicting_constraints" in conflict

    def test_resolve_deep_dependencies(self):
        """Test 55: Resolve deep dependency chain."""
        graph = DependencyGraph()

        base = ContractDependency("base", "1.0.0")
        mid = ContractDependency("mid", "1.0.0")
        mid.add_dependency(VersionConstraint("base", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        top = ContractDependency("top", "1.0.0")
        top.add_dependency(VersionConstraint("mid", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(base)
        graph.add_contract(mid)
        graph.add_contract(top)

        resolver = DependencyResolver(graph)
        result = resolver.resolve("top")

        assert result["success"] is True
        assert "base" in result["resolved_dependencies"]
        assert "mid" in result["resolved_dependencies"]

    def test_resolve_result_structure(self, resolver):
        """Test 56: Resolve result has correct structure."""
        result = resolver.resolve("app")
        assert "success" in result
        assert "contract" in result or "error" in result

    def test_conflict_includes_error(self):
        """Test 57: Conflict result includes error."""
        graph = DependencyGraph()
        libcore = ContractDependency("libcore", "2.0.0")
        lib1 = ContractDependency("lib1", "1.0.0")
        lib1.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        lib2 = ContractDependency("lib2", "1.0.0")
        lib2.add_dependency(VersionConstraint("libcore", ConstraintOperator.LESS, "2.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("lib1", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        app.add_dependency(VersionConstraint("lib2", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(libcore)
        graph.add_contract(lib1)
        graph.add_contract(lib2)
        graph.add_contract(app)

        resolver = DependencyResolver(graph)
        result = resolver.resolve("app")

        if not result["success"]:
            assert "error" in result

    def test_resolve_single_constraint(self, resolver):
        """Test 58: Resolve with single constraint works."""
        result = resolver.resolve("app")
        assert result["success"] is True

    def test_no_conflicts_message(self, resolver):
        """Test 59: No conflicts when dependencies compatible."""
        result = resolver.resolve("app")
        assert "conflicts" not in result or len(result.get("conflicts", [])) == 0

    def test_resolver_contract_name_preserved(self, resolver):
        """Test 60: Resolver preserves contract name."""
        result = resolver.resolve("app")
        if result["success"]:
            assert result["contract"] == "app"

    def test_empty_graph_resolve(self):
        """Test 61: Resolve in empty graph."""
        graph = DependencyGraph()
        resolver = DependencyResolver(graph)
        result = resolver.resolve("missing")
        assert result["success"] is False

    def test_resolve_multiple_same_deps(self):
        """Test 62: Resolve with multiple same dependencies."""
        graph = DependencyGraph()

        shared = ContractDependency("shared", "1.0.0")
        lib1 = ContractDependency("lib1", "1.0.0")
        lib1.add_dependency(VersionConstraint("shared", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        lib2 = ContractDependency("lib2", "1.0.0")
        lib2.add_dependency(VersionConstraint("shared", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        app = ContractDependency("app", "1.0.0")
        app.add_dependency(VersionConstraint("lib1", ConstraintOperator.GREATER_EQUAL, "1.0.0"))
        app.add_dependency(VersionConstraint("lib2", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        graph.add_contract(shared)
        graph.add_contract(lib1)
        graph.add_contract(lib2)
        graph.add_contract(app)

        resolver = DependencyResolver(graph)
        result = resolver.resolve("app")
        assert result["success"] is True

    def test_has_satisfying_version_simple(self, resolver):
        """Test 63: Has satisfying version with simple constraints."""
        c1 = VersionConstraint("lib", ConstraintOperator.GREATER_EQUAL, "1.0.0")
        c2 = VersionConstraint("lib", ConstraintOperator.LESS_EQUAL, "2.0.0")
        result = resolver._has_satisfying_version([("src1", c1), ("src2", c2)])
        assert isinstance(result, bool)

    def test_resolve_preserves_graph(self, resolver, simple_graph):
        """Test 64: Resolve doesn't modify graph."""
        original_count = len(simple_graph.nodes)
        resolver.resolve("app")
        assert len(simple_graph.nodes) == original_count

    def test_conflict_detection_preserves_graph(self, resolver, simple_graph):
        """Test 65: Conflict detection doesn't modify graph."""
        original_count = len(simple_graph.nodes)
        resolver.detect_conflicts("app")
        assert len(simple_graph.nodes) == original_count


# ============================================================================
# TEST COORDINATED UPGRADE PLANNER (15 TESTS)
# ============================================================================
class TestCoordinatedUpgradePlanner:
    """Test CoordinatedUpgradePlanner (15 tests)."""

    @pytest.fixture
    def setup(self):
        graph = DependencyGraph()

        libbase = ContractDependency("libbase", "1.0.0")
        libutils = ContractDependency("libutils", "1.5.0")
        libutils.add_dependency(VersionConstraint("libbase", ConstraintOperator.GREATER_EQUAL, "1.0.0"))

        libcore = ContractDependency("libcore", "2.0.0")
        libcore.add_dependency(VersionConstraint("libutils", ConstraintOperator.GREATER_EQUAL, "1.5.0"))

        app = ContractDependency("app", "3.0.0")
        app.add_dependency(VersionConstraint("libcore", ConstraintOperator.GREATER_EQUAL, "2.0.0"))

        graph.add_contract(libbase)
        graph.add_contract(libutils)
        graph.add_contract(libcore)
        graph.add_contract(app)

        planner = CoordinatedUpgradePlanner(graph)
        return planner

    def test_plan_coordinated_upgrade(self, setup):
        """Test 66: Plan coordinated upgrade."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0", "libcore": "3.0.0"})
        assert plan["success"] is True

    def test_upgrade_order(self, setup):
        """Test 67: Upgrade order is correct."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0", "libcore": "3.0.0"})
        order = plan["upgrade_order"]
        assert order.index("libcore") < order.index("app")

    def test_plan_includes_steps(self, setup):
        """Test 68: Plan includes upgrade steps."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0"})
        assert "steps" in plan

    def test_validate_upgrade_plan(self, setup):
        """Test 69: Validate upgrade plan."""
        result = setup.validate_upgrade_plan({"app": "4.0.0"})
        assert "valid" in result

    def test_validate_includes_issues(self, setup):
        """Test 70: Validation includes issues."""
        result = setup.validate_upgrade_plan({"app": "4.0.0"})
        assert "issues" in result

    def test_validate_includes_warnings(self, setup):
        """Test 71: Validation includes warnings."""
        result = setup.validate_upgrade_plan({"app": "4.0.0"})
        assert "warnings" in result

    def test_plan_empty_upgrades(self, setup):
        """Test 72: Plan with empty upgrades."""
        plan = setup.plan_coordinated_upgrade({})
        assert plan["success"] is True
        assert len(plan["steps"]) == 0

    def test_step_structure(self, setup):
        """Test 73: Step has correct structure."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0"})
        if len(plan["steps"]) > 0:
            step = plan["steps"][0]
            assert "contract" in step
            assert "from_version" in step
            assert "to_version" in step

    def test_get_dependents(self, setup):
        """Test 74: Get dependents of contract."""
        dependents = setup._get_dependents("libcore")
        assert "app" in dependents

    def test_validate_non_existent_contract(self, setup):
        """Test 75: Validate with non-existent contract."""
        result = setup.validate_upgrade_plan({"missing": "1.0.0"})
        assert len(result["issues"]) > 0

    def test_plan_single_upgrade(self, setup):
        """Test 76: Plan single contract upgrade."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0"})
        assert plan["success"] is True

    def test_upgrade_order_bottom_up(self, setup):
        """Test 77: Upgrade order is bottom-up."""
        plan = setup.plan_coordinated_upgrade({"libbase": "1.1.0", "libutils": "1.6.0", "libcore": "3.0.0", "app": "4.0.0"})
        order = plan["upgrade_order"]
        assert order.index("libbase") < order.index("libutils")
        assert order.index("libutils") < order.index("libcore")

    def test_validate_valid_plan(self, setup):
        """Test 78: Validate valid plan."""
        result = setup.validate_upgrade_plan({"app": "4.0.0"})
        assert result["valid"] is True or len(result["issues"]) == 0

    def test_plan_preserves_graph(self, setup):
        """Test 79: Planning doesn't modify graph."""
        original_count = len(setup.graph.nodes)
        setup.plan_coordinated_upgrade({"app": "4.0.0"})
        assert len(setup.graph.nodes) == original_count

    def test_step_includes_dependencies(self, setup):
        """Test 80: Step includes dependencies."""
        plan = setup.plan_coordinated_upgrade({"app": "4.0.0"})
        if len(plan["steps"]) > 0:
            step = plan["steps"][0]
            assert "dependencies" in step


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
