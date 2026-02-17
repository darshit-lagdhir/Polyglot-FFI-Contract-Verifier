# Contract Versioning Integration Guide

## Integration with Existing Systems

### 1. Integration with Binding Generators

```python
# In your binding generator:
from modules.module_06_contract_schema.contract_versioning import (
    ContractFingerprintComputer,
    VersionMetadata
)
from datetime import datetime, timezone

class BindingGenerator:
    def __init__(self):
        self.fingerprint_gen = ContractFingerprintComputer()
    
    def generate_bindings(self, contract, version):
        # Generate fingerprint
        fingerprint = self.fingerprint_gen.compute_fingerprint(contract)
        
        # Embed version metadata in bindings
        metadata = f"""
        // Contract Version: {version}
        // Fingerprint: {fingerprint}
        // Generated: {datetime.now(timezone.utc).isoformat()}
        """
        
        # Generate actual bindings...
        return bindings
```

### 2. Integration with CI/CD Pipeline

```yaml
# .github/workflows/contract-versioning.yml
name: Contract Versioning Check

on:
  pull_request:
    paths:
      - 'contracts/**'

jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check Contract Changes
        run: |
          python scripts/check_contract_version.py \
            --baseline origin/main \
            --candidate HEAD \
            --enforce-policy
```

```python
# scripts/check_contract_version.py
import sys
from modules.module_06_contract_schema.contract_versioning import (
    DetailedDiffAnalyzer,
    VersionPolicyEnforcer,
    VersionPolicy
)

def main():
    # baseline = load_contract(args.baseline)
    # candidate = load_contract(args.candidate)
    
    analyzer = DetailedDiffAnalyzer()
    # diff = analyzer.analyze(baseline, candidate)
    
    if args.enforce_policy:
        policy = VersionPolicy('strict')
        enforcer = VersionPolicyEnforcer(policy)
        
        # result = enforcer.enforce(
        #     current_version,
        #     proposed_version,
        #     diff
        # )
        
        # if not result['approved']:
        #     print("❌ Policy violations detected:")
        #     for violation in result['violations']:
        #         print(f"  - {violation}")
        #     sys.exit(1)
    
    print("✅ Version check passed")

if __name__ == '__main__':
    main()
```

### 3. Integration with Package Registry

```python
# Package registry integration
from modules.module_06_contract_schema.contract_versioning import (
    VersionManager,
    VersionValidator,
    ContractFingerprintComputer,
    VersionSnapshot
)
from datetime import datetime, timezone

class ContractRegistry:
    def __init__(self):
        self.version_manager = VersionManager()
    
    def publish_contract(self, contract, version, metadata):
        # Validate version
        validator = VersionValidator()
        validation = validator.validate_format(version)
        
        if not validation['valid']:
            raise ValueError(f"Invalid version: {validation['error']}")
        
        # Generate fingerprint
        fingerprint = ContractFingerprintComputer().compute_fingerprint(contract)
        
        # Store in registry
        # self.store(contract, version, fingerprint, metadata)
        
        # Update version history
        snapshot = VersionSnapshot(
            version=version,
            timestamp=datetime.now(timezone.utc).isoformat() + 'Z',
            fingerprint=fingerprint,
            contract_data=contract.to_dict() if hasattr(contract, 'to_dict') else {}
        )
        self.version_manager.version_history.add_snapshot(snapshot)
```

### 4. Integration with API Gateway

```python
# API Gateway with version negotiation
from modules.module_06_contract_schema.contract_versioning import (
    CompatibilityMatrix,
    CompatibilityStatus
)

class APIGateway:
    def __init__(self):
        self.compatibility_matrix = CompatibilityMatrix()
    
    def route_request(self, request):
        client_version = request.headers.get('X-Contract-Version')
        server_version = self.get_current_version()
        
        # Check compatibility
        compat = self.compatibility_matrix.get_compatibility(
            'client',
            client_version,
            'server',
            server_version
        )
        
        if not compat or compat.status == CompatibilityStatus.INCOMPATIBLE:
            return {
                'error': 'Incompatible versions',
                'client_version': client_version,
                'server_version': server_version,
                'upgrade_required': True
            }
        
        # Route to appropriate handler
        return self.handle_request(request, compat)
```

## Database Schema

For persistent storage of versioning data:

```sql
-- Version metadata
CREATE TABLE contract_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    lifecycle_stage VARCHAR(50),
    support_tier VARCHAR(50),
    metadata JSONB,
    UNIQUE(contract_name, version)
);

-- Version history
CREATE TABLE version_snapshots (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    parent_version VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    contract_data JSONB NOT NULL,
    FOREIGN KEY (version) REFERENCES contract_versions(version)
);

-- Compatibility matrix
CREATE TABLE version_compatibility (
    id SERIAL PRIMARY KEY,
    contract_a VARCHAR(255) NOT NULL,
    version_a VARCHAR(50) NOT NULL,
    contract_b VARCHAR(255) NOT NULL,
    version_b VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    tested_at TIMESTAMP NOT NULL,
    test_results JSONB
);

-- Provenance tracking
CREATE TABLE version_provenance (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    signature TEXT,
    signer_email VARCHAR(255),
    approval_chain JSONB,
    FOREIGN KEY (version) REFERENCES contract_versions(version)
);
```

## REST API Endpoints

Example REST API for version management:

```python
from flask import Flask, request, jsonify
from modules.module_06_contract_schema.contract_versioning import (
    IntegratedVersioningSystem,
    Author
)

app = Flask(__name__)
system = IntegratedVersioningSystem()

@app.route('/api/versions/<version>', methods=['GET'])
def get_version(version):
    """Get version information."""
    info = system.version_manager.get_version_info(version)
    return jsonify(info)

@app.route('/api/versions', methods=['POST'])
def release_version():
    """Release new version."""
    data = request.json
    
    author = Author(
        name=data['author']['name'],
        email=data['author']['email']
    )
    
    result = system.release_version(
        current_version=data['current_version'],
        candidate_contract=data['contract'],
        author=author
    )
    
    return jsonify(result), 201 if result['success'] else 400

@app.route('/api/versions/upgrade', methods=['POST'])
def upgrade_version():
    """Plan or execute version upgrade."""
    data = request.json
    
    if data.get('plan_only'):
        plan = system.upgrade_workflow.plan_upgrade(
            data['from_version'],
            data['to_version']
        )
        return jsonify(plan)
    else:
        result = system.upgrade_version(
            data['from_version'],
            data['to_version']
        )
        return jsonify(result)
```

## Monitoring & Metrics

```python
# Prometheus metrics example
# (Conceptual integration)
def release_with_metrics(version, contract, author):
    result = system.release_version(version, contract, author)
    
    if result['success']:
        # Logic to increment counters...
        pass
    
    return result
```
