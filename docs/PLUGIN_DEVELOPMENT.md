# Plugin Development Guide

Extend the Verification Pipeline with domain-specific logic.

## Plugin Structure

A plugin is a class inheriting from `PipelinePlugin`:

```python
from modules.module_02_verification_pipeline.verification_pipeline import PipelinePlugin

class MyPlugin(PipelinePlugin):
    PLUGIN_NAME = "my_plugin"
    PLUGIN_VERSION = "1.0.0"
    
    def initialize(self, pipeline):
        """Called when plugin is registered."""
        self.pipeline = pipeline
        
    def register_rules(self, registry):
        """Register custom constraint rules."""
        pass
        
    def get_hooks(self):
        """Return a dict of hooks."""
        return {}
```

## Registering Rules

Rules allow the **Contract Synthesis** stage to recognize your patterns:

```python
def register_rules(self, registry):
    registry.register(
        rule_id="crypto_buffer",
        constraint_class=CryptoConstraint,
        heuristic=lambda p: "key" in p.name or "iv" in p.name
    )
```

## Using Hooks

Hooks allow you to intercept and modify artifacts:

```python
def get_hooks(self):
    return {
        "post_ir_normalization": self.add_custom_types,
        "post_report_generation": self.notify_slack
    }

def add_custom_types(self, context, ir_data):
    # Modify IR data here
    pass
```

## Deployment

Simply pass the plugin instance to `verify_extensible`:

```python
result = verify_extensible(
    "api.h", "lib.dll",
    plugins=[MyPlugin()]
)
```
