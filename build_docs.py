#!/usr/bin/env python3
"""
Build script to create SYSTEM_ARCHITECTURE.md from all documentation files.

This script consolidates all 19 documentation files into a single comprehensive
reference document.
"""

import os
from pathlib import Path
from datetime import datetime

# Documentation files in logical order
DOCS_IN_ORDER = [
    # System Overview (from README)
    ('README.md', '1. SYSTEM OVERVIEW', 'root'),
    
    # Phase Implementations
    ('docs/ORCHESTRATION_IMPLEMENTATION.md', '3.1 : Execution Context & Orchestration', 'docs'),
    ('docs/INGESTION_IMPLEMENTATION.md', '3.2 : Native Interface Ingestion', 'docs'),
    ('docs/IR_NORMALIZATION_IMPLEMENTATION.md', '3.3 : IR Normalization', 'docs'),
    ('docs/CONTRACT_SYNTHESIS_IMPLEMENTATION.md', '3.4 : Contract Synthesis', 'docs'),
    ('docs/CONTRACT_VERSIONING_IMPLEMENTATION.md', '3.5 : Contract Versioning', 'docs'),
    ('docs/ADAPTER_GENERATION_IMPLEMENTATION.md', '3.6 : Adapter Generation', 'docs'),
    ('docs/TEST_PLAN_GENERATION_IMPLEMENTATION.md', '3.7 : Test Plan Generation', 'docs'),
    ('docs/VERIFICATION_EXECUTION_IMPLEMENTATION.md', '3.8 : Verification Execution', 'docs'),
    ('docs/RUNTIME_MONITORING_IMPLEMENTATION.md', '3.9 : Runtime Monitoring', 'docs'),
    ('docs/DIAGNOSTICS_MAPPING_IMPLEMENTATION.md', '3.10 0: Diagnostics Mapping', 'docs'),
    ('docs/REPORT_GENERATION_IMPLEMENTATION.md', '3.11 1: Report Generation', 'docs'),
    ('docs/CI_INTEGRATION.md', '3.12 2: CI/CD Integration', 'docs'),
    
    # Operational Guides
    ('docs/PERFORMANCE_CONSIDERATIONS.md', '4.1 Performance Considerations', 'docs'),
    ('docs/SECURITY_CONSIDERATIONS.md', '4.2 Security Considerations', 'docs'),
    ('docs/LIMITATIONS_AND_NON_GOALS.md', '4.3 Limitations and Non-Goals', 'docs'),
    ('docs/ERROR_HANDLING_PATTERNS.md', '4.4 Error Handling Patterns', 'docs'),
    ('docs/LOGGING_STRATEGY.md', '4.5 Logging Strategy', 'docs'),
    ('docs/BEST_PRACTICES.md', '4.6 Best Practices', 'docs'),
    
    # Integration
    ('docs/END_TO_END_VALIDATION.md', '5.2 End-to-End Validation', 'docs'),
]

def create_header():
    """Create document header."""
    return f'''# Polyglot FFI Contract Verifier
## Complete System Architecture and Technical Specification

**Version:** 1.0.0  
**Author:** Darshit Lagdhir  
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**License:** MIT

---

## Document Overview

This document provides a complete technical specification for the Polyglot FFI
Contract Verifier, consolidating all implementation documentation, operational
guides, and architectural decisions into a single comprehensive reference.

**Document Statistics:**
- Total Sections: 50+
- Source Documents: 19
- Consolidated: {datetime.now().strftime('%Y-%m-%d')}

**Reading Guide:**
- For quick overview: Read  (System Overview)
- For implementation details: Read  (Phase Implementations)
- For operational use: Read  (Operational Guides)
- For integration: Read  (Integration)

---

## Table of Contents

1. [SYSTEM OVERVIEW](#1-system-overview)
2. [PIPELINE ARCHITECTURE](#2-pipeline-architecture)
3. [PHASE IMPLEMENTATIONS](#3-phase-implementations)
   - 3.1 [: Execution Context & Orchestration](#31-phase-1-execution-context--orchestration)
   - 3.2 [: Native Interface Ingestion](#32-phase-2-native-interface-ingestion)
   - 3.3 [: IR Normalization](#33-phase-3-ir-normalization)
   - 3.4 [: Contract Synthesis](#34-phase-4-contract-synthesis)
   - 3.5 [: Contract Versioning](#35-phase-5-contract-versioning)
   - 3.6 [: Adapter Generation](#36-phase-6-adapter-generation)
   - 3.7 [: Test Plan Generation](#37-phase-7-test-plan-generation)
   - 3.8 [: Verification Execution](#38-phase-8-verification-execution)
   - 3.9 [: Runtime Monitoring](#39-phase-9-runtime-monitoring)
   - 3.10 [0: Diagnostics Mapping](#310-phase-10-diagnostics-mapping)
   - 3.11 [1: Report Generation](#311-phase-11-report-generation)
   - 3.12 [2: CI/CD Integration](#312-phase-12-cicd-integration)
4. [OPERATIONAL GUIDES](#4-operational-guides)
   - 4.1 [Performance Considerations](#41-performance-considerations)
   - 4.2 [Security Considerations](#42-security-considerations)
   - 4.3 [Limitations and Non-Goals](#43-limitations-and-non-goals)
   - 4.4 [Error Handling Patterns](#44-error-handling-patterns)
   - 4.5 [Logging Strategy](#45-logging-strategy)
   - 4.6 [Best Practices](#46-best-practices)
5. [INTEGRATION](#5-integration)
   - 5.1 [CI/CD Integration](#51-cicd-integration)
   - 5.2 [End-to-End Validation](#52-end-to-end-validation)
6. [APPENDICES](#6-appendices)

---

'''

def read_doc_file(filepath):
    """Read documentation file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Remove the title if it's the first line (we'll add our own section headers)
        lines = content.split('\n')
        if lines and lines[0].startswith('#'):
            lines = lines[1:]  # Skip first title line
        return '\n'.join(lines).strip()
    except FileNotFoundError:
        return f"*Documentation file not found: {filepath}*"

def create_section_header(section_number, section_title):
    """Create section header."""
    return f'''

---

## {section_number} {section_title}

'''

def build_documentation():
    """Build the complete SYSTEM_ARCHITECTURE.md file."""
    print("📚 Building SYSTEM_ARCHITECTURE.md...")
    
    output_lines = []
    
    # 1. Add header
    print("  ✓ Adding document header")
    output_lines.append(create_header())
    
    # 2. Add pipeline architecture section
    print("  ✓ Adding pipeline architecture")
    output_lines.append(create_section_header('2', 'PIPELINE ARCHITECTURE'))
    output_lines.append("""
The Polyglot FFI Contract Verifier is organized as a deterministic, artifact-driven pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Execution Context                            │
│  (Immutable environmental state for all stages)                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Native Interface Ingestion                            │
│  Input:  C header, library                                      │
│  Output: Native Interface Artifact (native_interface.json)      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: IR Normalization                                      │
│  Input:  Native Interface Artifact                              │
│  Output: Intermediate Representation (IR)                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Contract Synthesis                                    │
│  Input:  Intermediate Representation                            │
│  Output: FFI Contract                                           │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                          [Continue through all 12 phases...]
```

### Key Architectural Principles

1. **Immutability** - Once created, artifacts are never modified
2. **Explicitness** - No implicit assumptions or hidden behavior
3. **Determinism** - Identical inputs produce identical outputs
4. **Artifact-Driven** - All communication through explicit artifacts
5. **Failure Isolation** - Errors classified and handled appropriately
6. **Partial Execution** - Individual stages can be invoked independently
7. **Provenance Tracking** - Full traceability from inputs to outputs
""")
    
    # 3. Add Phase Implementations section header
    output_lines.append(create_section_header('3', 'PHASE IMPLEMENTATIONS'))
    
    # 4. Add each documentation file
    for doc_file, section_title, location in DOCS_IN_ORDER:
        filepath = doc_file if location == 'root' else doc_file
        
        print(f"  ✓ Adding {doc_file}")
        
        # Add section header
        output_lines.append(f"\n### {section_title}\n")
        
        # Add content
        content = read_doc_file(filepath)
        output_lines.append(content)
    
    # 5. Add Operational Guides header (already included in docs)
    output_lines.append(create_section_header('4', 'OPERATIONAL GUIDES'))
    output_lines.append("*See individual sections below for operational guidance.*\n")
    
    # 6. Add Integration header (already included in docs)
    output_lines.append(create_section_header('5', 'INTEGRATION'))
    output_lines.append("*See individual sections below for integration guidance.*\n")
    
    # 7. Add Appendices
    print("  ✓ Adding appendices")
    output_lines.append(create_section_header('6', 'APPENDICES'))
    output_lines.append("""
### 6.1 Glossary

**ABI** - Application Binary Interface  
**FFI** - Foreign Function Interface  
**IR** - Intermediate Representation  
**libclang** - C language family frontend for LLVM  
**ctypes** - Python foreign function interface library  
**MSVC** - Microsoft Visual C++ Compiler  
**Provenance** - Traceability of data origin and transformations  
**Artifact** - Immutable output file from a pipeline stage  

### 6.2 References

- [libclang documentation](https://libclang.readthedocs.io/)
- [Python ctypes documentation](https://docs.python.org/3/library/ctypes.html)
- [LLVM Project](https://llvm.org/)
- [Microsoft ABI Documentation](https://docs.microsoft.com/en-us/cpp/build/reference/)

### 6.3 History

**1.0.0** (2026-02-02)
- Initial release
- Complete 12-phase implementation
- Full documentation consolidation
- All 19 source documents merged

---

**End of System Architecture Documentation**

*This document was automatically created by consolidating 19 source documentation files.*  
*For the modular documentation (for development), see: docs/ directory*  
*For the modular code (for development), see: polyglot_ffi_verifier/ directory*  
*For the consolidated code, see: system_architecture.py*
""")
    
    # 8. Write to file
    output_file = 'SYSTEM_ARCHITECTURE.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    # 9. Report statistics
    total_lines = sum(1 for _ in open(output_file, 'r', encoding='utf-8'))
    file_size_kb = os.path.getsize(output_file) / 1024
    
    # Count words
    with open(output_file, 'r', encoding='utf-8') as f:
        word_count = len(f.read().split())
    
    print(f"\n✅ SUCCESS!")
    print(f"  File: {output_file}")
    print(f"  Lines: {total_lines:,}")
    print(f"  Words: {word_count:,}")
    print(f"  Size: {file_size_kb:.2f} KB")
    
    return output_file

if __name__ == '__main__':
    build_documentation()
