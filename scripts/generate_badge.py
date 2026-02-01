#!/usr/bin/env python3
"""
Generate status badge metadata for shields.io.

Usage:
    python scripts/generate_badge.py --output badges/ffi-status.json
"""

import json
import sys
import os
from pathlib import Path

# Fix path to include src/
sys.path.append(os.getcwd())

from src.ci.badge_generator import BadgeGenerator

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate status badge')
    parser.add_argument('--ci-summary', default='reports/ci_summary.json')
    parser.add_argument('--output', default='badges/ffi-status.json')
    args = parser.parse_args()
    
    if not os.path.exists(args.ci_summary):
        print(f"ERROR: CI summary not found at {args.ci_summary}")
        sys.exit(1)
        
    with open(args.ci_summary, 'r') as f:
        summary = json.load(f)
        
    gen = BadgeGenerator()
    badge = gen.generate_badge(summary)
    gen.write_badge_json(badge, args.output)
    
    print(f"Badge generated at {args.output}")
    print(f"  Message: {badge['message']}")
    print(f"  Color:  {badge['color']}")

if __name__ == '__main__':
    main()
