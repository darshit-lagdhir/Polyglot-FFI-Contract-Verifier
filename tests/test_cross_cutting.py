"""
Validation Script for Cross-Cutting Concerns
Checks for existence and completeness of 3 documentation.
"""

import os
import sys

def check_file(path, required_sections):
    if not os.path.exists(path):
        print(f"❌ Missing file: {path}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for section in required_sections:
        if section not in content:
            print(f"❌ Missing section '{section}' in {path}")
            return False
            
    print(f"✓ Checked {os.path.basename(path)}")
    return True

def test_cross_cutting_concerns():
    print("Testing Cross-Cutting Concerns Documentation...")
    
    docs_dir = "docs"
    
    # TEST 1: Performance Documentation
    if not check_file(os.path.join(docs_dir, "PERFORMANCE_CONSIDERATIONS.md"), [
        ": Orchestration", 
        "Scalability Limits"
    ]): return False
    print("✓ Performance documentation complete")

    # TEST 2: Security Documentation
    if not check_file(os.path.join(docs_dir, "SECURITY_CONSIDERATIONS.md"), [
        "Threat Model",
        "Attack Surface", 
        "Recommendations for Secure Usage"
    ]): return False
    print("✓ Security documentation complete")

    # TEST 3: Limitations Documentation
    if not check_file(os.path.join(docs_dir, "LIMITATIONS_AND_NON_GOALS.md"), [
        "Explicit Non-Goals",
        "Known Limitations",
        "When NOT to Use This Tool"
    ]): return False
    print("✓ Limitations documentation complete")

    # TEST 4: Error Handling Documentation
    if not check_file(os.path.join(docs_dir, "ERROR_HANDLING_PATTERNS.md"), [
        "Error Taxonomy",
        "Exception Hierarchy",
        "Recovery Strategies"
    ]): return False
    print("✓ Error handling documentation complete")

    # TEST 5: Logging Documentation
    if not check_file(os.path.join(docs_dir, "LOGGING_STRATEGY.md"), [
        "Logging Levels",
        "Log Output Channels",
        "Contextual Logging"
    ]): return False
    print("✓ Logging documentation complete")

    # TEST 6: Best Practices Documentation
    if not check_file(os.path.join(docs_dir, "BEST_PRACTICES.md"), [
        "For Users",
        "For Maintainers"
    ]): return False
    print("✓ Best practices documentation complete")

    print("\n✓ ALL TESTS PASSED (6/6)")
    return True

if __name__ == "__main__":
    if not test_cross_cutting_concerns():
        sys.exit(1)
