# Best Practices

Recommended patterns for effective FFI verification.

## General Principles

### 1. Start Simple

Begin with basic verification, then add customization:

```python
# First run: Basic verification
result = verify("interface.h", "library.dll")

# Later: Add optimizations
result = verify_optimized("interface.h", "library.dll", cache=True)

# Advanced: Add custom rules
result = verify_extensible("interface.h", "library.dll", plugins=[...])
```

### 2. Verify Early and Often

Integrate verification into development workflow:

- Run verification on every commit
- Include in CI/CD pipeline
- Verify before releases

### 3. Review Reports Carefully

Don't just check pass/fail:

- Understand why tests failed
- Review constraint coverage
- Check for missing edge cases

---

## Header Design

### Use Explicit Contracts

**Bad:**
```c
void process(char* data, int size);
```

**Good:**
```c
// Processes data buffer
// @param data: Non-null buffer of at least 'size' bytes
// @param size: Buffer size, must be > 0
void process(char* data, int size);
```

### Avoid Implicit Assumptions

**Bad:**
```c
int get_value(void* context);  // What is context
```

**Good:**
```c
typedef struct Config Config;
int get_value(Config* config);  // Clear type
```

### Use `const` Appropriately

```c
// Input parameter - use const
int process(const char* input, size_t length);

// Output parameter - no const
int read_data(char* output, size_t* length);
```

---

## Performance Optimization

### Enable Caching for Iterative Development

```python
# During development (fast iteration)
result = verify_optimized("interface.h", "library.dll", cache=True)
```

Cache invalidation happens automatically when:
- Header file changes
- Library file changes
- Pipeline version changes

### Use Parallelism for Large Codebases

```python
# For headers with 50+ functions
result = verify_optimized(
    "large_interface.h", "library.dll",
    parallel=True,
    max_workers=8  # Match CPU cores
)
```

### Profile to Identify Bottlenecks

```python
result = verify_optimized("interface.h", "library.dll", profile=True)
# Check performance.prof for slow stages
```

---

## Customization

### Create Reusable Plugins

Package domain-specific rules as plugins:

```python
# my_plugin.py
from verification_pipeline import PipelinePlugin

class DomainPlugin(PipelinePlugin):
    PLUGIN_NAME = "domain_rules"
    PLUGIN_VERSION = "1.0.0"
    
    def register_rules(self, registry):
        # Register domain-specific rules
        pass
```

Use across projects:
```python
from my_plugin import DomainPlugin

result = verify_extensible(
    "interface.h", "library.dll",
    plugins=[DomainPlugin()]
)
```

### Use Hooks for Custom Logic

```python
def log_contract(context, contract, **kwargs):
    """Log synthesized contract for review."""
    with open("contract_review.json", "w") as f:
        json.dump(contract, f, indent=2)

result = verify_extensible(
    "interface.h", "library.dll",
    hooks={"post_contract_synthesis": log_contract}
)
```

---

## CI/CD Integration

### Fail Fast on Critical Issues

```python
result = verify("interface.h", "library.dll")

if result.critical_issues:
    print("CRITICAL ISSUES:")
    for issue in result.critical_issues:
        print(f"  - {issue}")
    sys.exit(1)
```

### Upload Reports as Artifacts

**GitHub Actions:**
```yaml
- name: Run verification
  run: python verify.py

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v2
  with:
    name: verification-report
    path: artifacts/report.html
```

### Cache Verification Results

```yaml
- name: Cache verification
  uses: actions/cache@v2
  with:
    path: .verification_cache
    key: verification-${{ hashFiles('interface.h') }}
```

---

## Testing Strategy

### Test Positive and Negative Cases

Verification generates both:
- **Positive tests**: Valid inputs should succeed
- **Negative tests**: Invalid inputs should fail safely

Review both in the report.

### Supplement with Manual Tests

Verification is comprehensive but not exhaustive:

```python
# After verification, add manual edge cases
def test_my_edge_case():
    # Custom test logic
    pass
```

### Monitor Coverage

Check constraint coverage in report:
- Aim for >80% coverage
- Identify untested constraints
- Add custom tests for gaps

---

## Maintenance

### Keep Documentation Updated

When interface changes:
1. Update header comments
2. Re-run verification
3. Review new constraints
4. Update custom rules if needed

### Version Your Plugins

```python
class MyPlugin(PipelinePlugin):
    PLUGIN_VERSION = "1.2.0"  # Increment on changes
```

### Review Verification Regularly

Schedule periodic reviews:
- Monthly: Check for new edge cases
- Quarterly: Review custom rules
- Yearly: Audit entire verification setup

---

## Common Patterns

### Buffer + Length Pattern

```c
int process_buffer(const char* data, size_t length);
```

Verification automatically infers:
- `data` must not be null if `length > 0`
- `data` must point to buffer of at least `length` bytes

### Output Parameter Pattern

```c
int get_data(char** output, size_t* length);
```

Verification infers:
- `output` must not be null
- `length` must not be null
- Function allocates memory (caller must free)

### Handle Pattern

```c
typedef void* HANDLE;
int create_handle(HANDLE* handle);
int close_handle(HANDLE handle);
```

Add custom constraint:
```python
class HandleValidConstraint(CustomConstraint):
    def validate(self, value):
        return value is not None and value != -1
```

---

## Anti-Patterns to Avoid

### ❌ Ignoring Verification Failures

Don't just disable failing tests. Investigate and fix.

### ❌ Over-Customizing

Start with default behavior. Only customize when necessary.

### ❌ Not Reviewing Reports

The HTML report contains valuable insights. Always review it.

### ❌ Skipping Verification in CI

Verification should be part of every build.

---

## Summary

**Do:**
- ✓ Verify early and often
- ✓ Review reports carefully
- ✓ Use caching for speed
- ✓ Create reusable plugins
- ✓ Integrate with CI/CD

**Don't:**
- ✗ Ignore failures
- ✗ Over-customize
- ✗ Skip CI verification
- ✗ Forget to update docs
