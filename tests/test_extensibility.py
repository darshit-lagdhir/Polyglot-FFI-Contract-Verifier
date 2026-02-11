from verification_pipeline import (
    CustomConstraint,
    PipelinePlugin,
    RuleRegistry,
    HookManager,
    HookContext,
    HookPoints,
    PluginManager,
    RuleTemplates,
    verify_extensible,
)
import os
import sys

sys.path.insert(0, os.path.abspath("modules/module_02_verification_pipeline"))


def test_custom_constraint():
    print("Testing CustomConstraint...")

    class TestConstraint(CustomConstraint):
        CONSTRAINT_TYPE = "test_positive"

        def validate(self, value):
            return value is not None and value > 0

        def generate_check_code(self):
            return f"assert {self.target} > 0"

    constraint = TestConstraint("test_positive", "param_x", min_value=1)

    # Test validation
    assert constraint.validate(5)
    assert not constraint.validate(-1)
    assert not constraint.validate(None)
    print("  ✓ Custom constraint validation works")

    # Test serialization
    data = constraint.to_dict()
    assert data["type"] == "test_positive"
    assert data["target"] == "param_x"
    assert data["min_value"] == 1
    print("  ✓ Custom constraint serialization works")

    # Test code generation
    code = constraint.generate_check_code()
    assert "param_x" in code
    print("  ✓ Custom constraint code generation works")

    print("✓ CustomConstraint tests passed\n")


def test_rule_registry():
    """Test rule registry."""
    print("Testing RuleRegistry...")

    registry = RuleRegistry()

    # Register rule
    class DummyConstraint:
        pass

    registry.register(
        "test_rule",
        DummyConstraint,
        synthesis_heuristic=lambda ctx: ctx.get("applies", False),
        priority=10,
    )

    assert "test_rule" in registry.list_rules()
    print("  ✓ Rule registration works")

    # Test duplicate registration
    try:
        registry.register("test_rule", DummyConstraint)
        raise AssertionError("Should have raised ValueError")
    except ValueError:
        print("  ✓ Duplicate rule detection works")

    # Test applicable rules
    applicable = registry.get_applicable_rules({"applies": True})
    assert len(applicable) == 1
    assert applicable[0]["rule_id"] == "test_rule"
    print("  ✓ Applicable rule detection works")

    # Test priority sorting (use None heuristic so all apply)
    registry.register("high_priority", DummyConstraint, synthesis_heuristic=None, priority=20)
    registry.register("low_priority", DummyConstraint, synthesis_heuristic=None, priority=5)

    applicable = registry.get_applicable_rules({})
    # Only rules with None heuristic apply (test_rule has heuristic that
    # returns False)
    assert len(applicable) == 2
    assert applicable[0]["rule_id"] == "high_priority"
    assert applicable[1]["rule_id"] == "low_priority"
    print("  ✓ Priority sorting works")

    print("✓ RuleRegistry tests passed\n")


def test_hook_manager():
    """Test hook manager."""
    print("Testing HookManager...")

    manager = HookManager()

    # Register hooks
    executed = []

    def hook1(context, **kwargs):
        executed.append("hook1")

    def hook2(context, **kwargs):
        executed.append("hook2")

    manager.register(HookPoints.PRE_PIPELINE, hook1)
    manager.register(HookPoints.PRE_PIPELINE, hook2)

    # List hooks
    hooks = manager.list_hooks()
    assert hooks[HookPoints.PRE_PIPELINE] == 2
    print("  ✓ Hook registration works")

    # Execute hooks
    context = HookContext("test-id", None, {})
    manager.execute(HookPoints.PRE_PIPELINE, context)

    assert len(executed) == 2
    assert "hook1" in executed
    assert "hook2" in executed
    print("  ✓ Hook execution works")

    def failing_hook(context, **kwargs):
        raise ValueError("Hook failed")

    manager.register(HookPoints.POST_PIPELINE, failing_hook)
    manager.execute(HookPoints.POST_PIPELINE, context)
    print("  ✓ Hook failure handling works")

    print("✓ HookManager tests passed\n")


def test_plugin_interface():
    """Test plugin interface."""
    print("Testing PipelinePlugin...")

    class TestPlugin(PipelinePlugin):
        PLUGIN_NAME = "test_plugin"
        PLUGIN_VERSION = "1.0.0"
        PLUGIN_AUTHOR = "Test Author"

        def __init__(self):
            self.initialized = False

        def initialize(self, pipeline):
            self.initialized = True

        def get_hooks(self):
            return {HookPoints.PRE_PIPELINE: lambda ctx, **kw: None}

    plugin = TestPlugin()
    assert plugin.PLUGIN_NAME == "test_plugin"
    assert plugin.PLUGIN_VERSION == "1.0.0"
    print("  ✓ Plugin attributes work")

    # Test initialization
    plugin.initialize(None)
    assert plugin.initialized
    print("  ✓ Plugin initialization works")

    # Test hooks
    hooks = plugin.get_hooks()
    assert HookPoints.PRE_PIPELINE in hooks
    print("  ✓ Plugin hooks work")

    print("✓ PipelinePlugin tests passed\n")


def test_plugin_manager():
    """Test plugin manager."""
    print("Testing PluginManager...")

    class MockPipeline:
        def __init__(self):
            self.registry = None
            self.rule_registry = RuleRegistry()
            self.hook_manager = HookManager()

    class ValidPlugin(PipelinePlugin):
        PLUGIN_NAME = "valid"
        PLUGIN_VERSION = "1.0.0"

        def initialize(self, pipeline):
            pass

    pipeline = MockPipeline()
    manager = PluginManager(pipeline)

    # Register valid plugin
    plugin = ValidPlugin()
    manager.register_plugin(plugin)

    plugins = manager.list_plugins()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "valid"
    print("  ✓ Plugin registration works")

    # Test invalid plugin
    class InvalidPlugin:
        pass

    try:
        manager.register_plugin(InvalidPlugin())
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "validation failed" in str(e).lower()
        print("  ✓ Plugin validation works")

    print("✓ PluginManager tests passed\n")


def test_rule_templates():
    """Test rule templates."""
    print("Testing RuleTemplates...")

    # Test pointer_not_null template
    rule = RuleTemplates.pointer_not_null("buffer")
    assert rule["type"] == "NON_NULL"
    assert "buffer" in rule["target"]
    print("  ✓ pointer_not_null template works")

    # Test buffer_with_length template
    rule = RuleTemplates.buffer_with_length("data", "size")
    assert rule["type"] == "BUFFER_SIZE"
    assert "data" in rule["target"]
    assert "size" in rule["related_target"]
    print("  ✓ buffer_with_length template works")

    # Test output_parameter template
    rule = RuleTemplates.output_parameter("result")
    assert rule["type"] == "OUTPUT_PARAMETER"
    assert "result" in rule["target"]
    print("  ✓ output_parameter template works")

    print("✓ RuleTemplates tests passed\n")


def test_extensible_api():
    print("Testing verify_extensible API...")

    assert callable(verify_extensible)
    print("  ✓ verify_extensible() API available")

    try:
        verify_extensible("nonexistent.h", "nonexistent.dll")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        print("  ✓ Correctly caught missing input files")

    print("✓ Extensible API tests passed\n")


if __name__ == "__main__":
    test_custom_constraint()
    test_rule_registry()
    test_hook_manager()
    test_plugin_interface()
    test_plugin_manager()
    test_rule_templates()
    test_extensible_api()

    print("=" * 60)
    print("ALL EXTENSIBILITY TESTS PASSED")
    print("=" * 60)
