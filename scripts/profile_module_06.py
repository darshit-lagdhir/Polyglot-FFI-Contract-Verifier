""" 
Profiling script for Module 06.
Runs cProfile on key operations and generates reports. 
"""

import cProfile
import pstats
import sys
from pathlib import Path
from io import StringIO
import os

# Add modules to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'modules'))

from module_06_contract_schema import (
    ContractGenerator,
    ContractValidator,
    ContractDocument,
    ContractHeader,
    ContractClause,
    SubjectReference,
    SubjectKind,
    ClauseType
)

def create_large_contract(n_clauses=1000):
    """Create large contract for profiling."""
    header = ContractHeader(target_interface_id="profile_test")
    contract = ContractDocument(header=header)
    
    for i in range(n_clauses):
        ref = SubjectReference(SubjectKind.FUNCTION, f"func_{i}")
        clause = ContractClause(f"clause_{i}", ClauseType.SIZE, ref)
        contract.add_clause(clause)
        
    return contract

def profile_generation():
    """Profile contract generation."""
    generator = ContractGenerator()
    # Mock IR handled inside generate prototype
    contract = generator.generate(None, "profile_interface")
    return contract

def profile_validation():
    """Profile contract validation."""
    contract = create_large_contract(500)
    validator = ContractValidator()
    result = validator.validate(
        contract,
        skip_referential=True,
        skip_constraint=True
    )
    return result

def run_profile(func, name):
    """Run profiler on function and print results."""
    print(f"\n{'='*80}")
    print(f"Profiling: {name}")
    print(f"{'='*80}")
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func()
    
    profiler.disable()
    
    # Print stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    print(s.getvalue())
    
    return result

def main():
    """Run all profiles."""
    print("Module 06 Performance Profiling")
    print("="*80)
    
    # Profile generation
    run_profile(profile_generation, "Contract Generation")
    
    # Profile validation
    run_profile(profile_validation, "Contract Validation")
    
    print(f"\n{'='*80}")
    print("Profiling complete")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
