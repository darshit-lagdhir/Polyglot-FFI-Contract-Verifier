#!/bin/bash
# build_dist.sh - Build source and wheel distributions

set -e

echo "Cleaning dist/ directory..."
rm -rf dist/ build/ *.egg-info

echo "Installing build tools..."
pip install --upgrade pip build

echo "Building distributions..."
python -m build

echo ""
echo "Distributions built in dist/:"
ls -lh dist/
