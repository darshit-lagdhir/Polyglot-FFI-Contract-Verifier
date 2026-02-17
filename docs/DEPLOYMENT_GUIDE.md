# Production Deployment Guide

Guide to deploying Language Adapter in production environments.

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (2,220+ tests)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No critical TODOs remaining

### Configuration
- [ ] Production config created
- [ ] Logging configured (ERROR level recommended)
- [ ] Metrics endpoint configured
- [ ] Caching enabled for performance

### Security
- [ ] Security review completed
- [ ] Dependencies up to date
- [ ] No hardcoded secrets
- [ ] Input validation comprehensive

### Performance
- [ ] Benchmarks performed and reviewed
- [ ] Performance meets SLOs
- [ ] Caching tuned for production load
- [ ] Fast paths verified

## Configuration

### Production Configuration
```python
from language_adapter import AdapterConfiguration, EnforcementPolicy

config = AdapterConfiguration(
    enforcement_policy=EnforcementPolicy.balanced(),
    verbose_logging=False,           # Only log errors/critical events
    trace_validation=False,          # Disable for performance
)

adapter = create_adapter('contract.json', config=config)
adapter.enable_caching()  # Essential for production latency
```

### Logging Configuration
```python
import logging

# Configure logging according to company standards
logging.basicConfig(
    level=logging.ERROR,  # High threshold for production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Monitoring

### Key Metrics
Monitor the following metrics to ensure healthy operation:
- `adapter.invocations.total` - Total count of FFI calls
- `adapter.violations.total` - Count of contract violations
- `adapter.errors.total` - Internal error count
- `adapter.invocations.duration_ms` - Latency distribution

### Health Checks
```python
def health_check():
    """Health check endpoint for orchestration."""
    try:
        # Simple test call
        adapter.call_with_enforcement('internal_status')
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Alerting
Configure alerts for:
- **High violation rate** (>5% of traffic)
- **High internal error rate** (>1% of traffic)
- **Degraded performance** (p95 latency > 100ms)
- **Memory anomalies** (unexpected growth in tracked buffers)

## Deployment Patterns

### Blue-Green Deployment
1. Deploy new version to "Green" environment.
2. Run automated smoke tests against Green.
3. Switch traffic from Blue to Green.
4. Monitor violation rates closely during the first hour.

### Canary Deployment
```python
# Gradual rollout logic
rollout_percentage = 10  # Start with 10% of traffic

if random.random() < rollout_percentage / 100:
    # Route to new adapter logic
    adapter = create_adapter_v2()
else:
    # Route to stable adapter logic
    adapter = create_adapter_v1()
```

## Troubleshooting
See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed issue resolution steps.

## Rollback Plan
1. Switch traffic back to the previous stable version immediately if `adapter.errors.total` spikes.
2. Capture a state snapshot for offline diagnostics: `persistence_manager.save_state(adapter, 'crash_dump.json')`.
3. Investigate root cause using captured diagnostics.
