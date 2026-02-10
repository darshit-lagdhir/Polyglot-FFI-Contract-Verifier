# API Reference

Complete API documentation for the Polyglot FFI Verification Pipeline.

## High-Level Functions

### verify()

Run complete verification pipeline.

```python
def verify(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    verbose: bool = True
) -> VerificationResult
```

**Parameters:**
- `header_path` (str): Path to C header file
- `library_path` (str): Path to native library
- `output_dir` (str): Output directory for artifacts (default: "artifacts")
- `verbose` (bool): Show progress messages (default: True)

**Returns:**
- `VerificationResult`: Result object with summary and paths

**Example:**

```python
result = verify("interface.h", "library.dll")
if result.success:
    print(f"Passed: {result.pass_rate}%")
```

---

### verify_optimized()

Optimized verification with caching and parallelism.

```python
def verify_optimized(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    verbose: bool = True,
    cache: bool = True,
    parallel: bool = False,
    max_workers: int = 4,
    profile: bool = False
) -> VerificationResult
```

**Parameters:**
- All parameters from `verify()`, plus:
- `cache` (bool): Enable artifact caching (default: True)
- `parallel` (bool): Enable parallel stage execution (default: False)
- `max_workers` (int): Maximum parallel workers (default: 4)
- `profile` (bool): Enable performance profiling (default: False)

**Example:**

```python
result = verify_optimized(
    "interface.h", "library.dll",
    cache=True,
    parallel=True,
    max_workers=8
)
```

---

### verify_extensible()

Extensible verification with plugins and hooks.

```python
def verify_extensible(
    header_path: str,
    library_path: str,
    output_dir: str = "artifacts",
    plugins: Optional[List[PipelinePlugin]] = None,
    hooks: Optional[Dict[str, Callable]] = None,
    custom_rules: Optional[Dict] = None,
    **kwargs
) -> VerificationResult
```

**Parameters:**
- All parameters from `verify_optimized()`, plus:
- `plugins` (List[PipelinePlugin]): Plugins to register
- `hooks` (Dict[str, Callable]): Hooks to register
- `custom_rules` (Dict): Custom rules to register

**Example:**

```python
result = verify_extensible(
    "interface.h", "library.dll",
    plugins=[MyPlugin()],
    hooks={"post_contract_synthesis": my_hook}
)
```

---

## Classes

### VerificationResult

Result of verification pipeline execution.

**Attributes:**
- `success` (bool): Overall pass/fail
- `pass_rate` (float): Percentage of tests passed
- `total_tests` (int): Total tests executed
- `passed_tests` (int): Tests that passed
- `failed_tests` (int): Tests that failed
- `critical_issues` (List[str]): Critical failure messages
- `execution_time` (float): Total time in seconds
- `report_path` (str): Path to HTML report
- `artifacts_dir` (str): Path to artifacts directory
- `stages_completed` (List[str]): Stages that finished
- `error` (Optional[Exception]): Error if pipeline failed

**Methods:**
- `__str__()`: Human-readable summary

---


Base class for custom user-defined constraints.

```python
class CustomConstraint(ABC):
    CONSTRAINT_TYPE: str
    
    def __init__(self, constraint_type: str, target: str, **metadata)
    
    @abstractmethod
    def validate(self, value: Any) -> bool
    
    @abstractmethod
    def generate_check_code(self) -> str
    
    def to_dict(self) -> Dict[str, Any]
```

**Example:**

```python
class MyConstraint(CustomConstraint):
    CONSTRAINT_TYPE = "my_constraint"
    
    def validate(self, value):
        return value > 0
    
    def generate_check_code(self):
        return "if value <= 0: raise Error()"
```

---

### PipelinePlugin

Base class for pipeline plugins.

```python
class PipelinePlugin(ABC):
    PLUGIN_NAME: str
    PLUGIN_VERSION: str
    PLUGIN_AUTHOR: str
    
    @abstractmethod
    def initialize(self, pipeline)
    
    def register_stages(self, registry)
    def register_rules(self, registry)
    def get_hooks(self) -> Dict[str, Callable]
```

**Example:**

```python
class MyPlugin(PipelinePlugin):
    PLUGIN_NAME = "my_plugin"
    PLUGIN_VERSION = "1.0.0"
    
    def initialize(self, pipeline):
        self.pipeline = pipeline
```

---

## Enumerations

### HookPoints

Available hook points in pipeline.

**Values:**
- `PRE_PIPELINE`: Before pipeline starts
- `POST_PIPELINE`: After pipeline completes
- `PIPELINE_ERROR`: On pipeline failure
- `PRE_STAGE`: Before each stage
- `POST_STAGE`: After each stage
- `POST_CONTRACT_SYNTHESIS`: After contract synthesis

---

## Command-Line Interface

### verify

Run complete verification.

```bash
python -m verification_pipeline verify <header> <library> [options]
```

**Options:**
- `--output DIR`: Output directory
- `--quiet`: Suppress progress messages

**Example:**

```bash
python -m verification_pipeline verify interface.h library.dll --output results/
```

---

### list-stages

List available pipeline stages.

```bash
python -m verification_pipeline list-stages
```

---

### info

Show pipeline information.

```bash
python -m verification_pipeline info
```
