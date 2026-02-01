#!/usr/bin/env python3
"""
Check CI summary and exit with appropriate code.

Usage:
    python scripts/check_ci_status.py [--strict]
"""

import json
import sys
import os
from pathlib import Path

# Fix path to include src/
sys.path.append(os.getcwd())

from src.ci.ci_status_checker import CIStatusChecker
from src.ci.configuration_manager import ConfigurationManager

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check CI status')
    parser.add_argument('--ci-summary', default='reports/ci_summary.json')
    parser.add_argument('--strict', action='store_true',
                       help='Fail on any violation, not just critical')
    parser.add_argument('--config', default='configs/ffi_verifier.yml')
    args = parser.parse_args()
    
    if not os.path.exists(args.ci_summary):
        print(f"ERROR: CI summary not found at {args.ci_summary}", file=sys.stderr)
        sys.exit(1)
        
    with open(args.ci_summary, 'r') as f:
        summary = json.load(f)
        
    config_mgr = ConfigurationManager()
    config = config_mgr.load_config(args.config)
    
    # Override strict mode from CLI if provided
    if args.strict:
        config['failure_policy']['strict_mode'] = True
        
    checker = CIStatusChecker()
    checker.print_ci_summary(summary)
    
    exit_code = checker.check_status(summary, config['failure_policy'])
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
