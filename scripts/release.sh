#!/bin/bash
# release.sh - Automated release script

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: ./release.sh [major|minor|patch]"
    exit 1
fi

BUMP_TYPE=$1

echo "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo "ERROR: Uncommitted changes found. Please commit or stash them first."
    exit 1
fi

echo "Running tests..."
pytest tests/ -v

echo "Bumping version..."
python scripts/bump_version.py $BUMP_TYPE
VERSION=$(python -c 'from src.polyglot_ffi_verifier.__version__ import __version__; print(__version__)')

echo "Building distributions..."
./scripts/build_dist.sh

echo "Committing version bump..."
git add src/polyglot_ffi_verifier/__version__.py pyproject.toml
git commit -m "chore: bump version to $VERSION"

echo "Tagging release..."
git tag -a v$VERSION -m "Version $VERSION"

echo "Pushing to origin..."
git push origin main --tags

echo ""
echo "Release v$VERSION prepared successfully!"
echo "Next step: twine upload dist/*"
