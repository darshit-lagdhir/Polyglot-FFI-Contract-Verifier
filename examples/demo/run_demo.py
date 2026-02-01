#!/usr/bin/env python3
"""
Automated demo script for FFI Contract Verifier.
Simulates the verification process on the vulnerable library.
"""

import sys
import os
import time
import json
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def run_demo():
    print("\n🚀 STARTING POLYGLOT FFI VERIFIER DEMO 🚀\n")
    time.sleep(1)
    
    base_dir = Path(__file__).parent
    header_path = base_dir / "interface.h"
    
    print(f"📂 Analyzing interface: {header_path.name}")
    print("   • Function: write_buffer(uint8_t* buffer, uint32_t size)")
    print("   • Function: process_config(struct Config* cfg)")
    time.sleep(1)
    
    print("\n🔍 Phase 1: Ingesting & Synthesizing Contracts")
    print("   ✓ Parsed C header")
    print("   ✓ Synthesized Contract:")
    print("     - Constraint: buffer length ≥ size")
    print("     - Constraint: cfg must not be NULL")
    time.sleep(1)
    
    print("\n🧪 Phase 2: Generating & Executing Tests")
    print("   → Generated 12 test cases")
    print("   → Running tests against native library...")
    time.sleep(0.5)
    print("     [PASS] write_buffer(buf[10], size=10)")
    time.sleep(0.2)
    print("     [PASS] write_buffer(buf[100], size=50)")
    time.sleep(0.2)
    print("     [FAIL] write_buffer(buf[5], size=100)  <-- CRASH DETECTED 💥")
    time.sleep(0.2)
    print("     [FAIL] process_config(NULL)            <-- CRASH DETECTED 💥")
    time.sleep(1)
    
    print("\n📊 Phase 3: Analyzing & Reporting")
    print("   ⚠ CRITICAL VULNERABILITY DETECTED")
    print("     Function: write_buffer")
    print("     Violation: Buffer Overflow Risk")
    print("     Details: Implementation writes 'size' bytes without verifying buffer capacity.")
    print("\n   ⚠ CRITICAL VULNERABILITY DETECTED")
    print("     Function: process_config")
    print("     Violation: Null Pointer Dereference")
    
    print("\n📝 Generating report...")
    time.sleep(1)
    print("   ✓ Report saved to: report.html")
    
    print("\n✅ DEMO COMPLETED SUCCESSFULLY")
    
    return True

if __name__ == "__main__":
    if run_demo():
        sys.exit(0)
    else:
        sys.exit(1)
