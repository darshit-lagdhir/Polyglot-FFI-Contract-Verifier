# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 4631e5797aad2c27
# ==============================================================================

echo ""

# Check we're on main branch (simulation)
# BRANCH=$(git branch --show-current)
# if [ "$BRANCH" != "main" ]; then
#     echo "Error: Must be on main branch (currently on $BRANCH)"
#     exit 1
# fi

# Check working directory is clean (simulation)
# if [ -n "$(git status --porcelain)" ]; then
#     echo "Error: Working directory is not clean"
#     git status --short
#     exit 1
# fi

# Run pre-release validation
echo "Running pre-release validation..."
python scripts/run_pre_release_validation.py
if [ $? -ne 0 ]; then
    echo "Error: Pre-release validation failed"
    exit 1
fi

echo ""
echo "✓ Pre-release validation passed"
echo ""

# Prompt for version
CUR_VER=$(python -c 'import sys; sys.path.append("modules"); from module_07_contract_synthesis.__version__ import __version__; print(__version__)')
echo "Current version: $CUR_VER"
echo ""
read -p "Enter new version (format: X.Y.Z): " NEW_VERSION

# Validate version format
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format"
    exit 1
fi

echo ""
echo "Preparing release v$NEW_VERSION..."
echo ""

# Update version (assumes bump_version.py exists)
echo "Updating version..."
python scripts/bump_version.py $NEW_VERSION

# Update changelog
echo "Update CHANGELOG.md with release date and notes"
echo "Press Enter when ready..."
read

# Build distributions
echo "Building distributions..."
python -m build

# Check distributions
echo "Checking distributions..."
twine check dist/*

echo ""
echo "✓ Release v$NEW_VERSION prepared"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit: git commit -am 'Release v$NEW_VERSION'"
echo "  3. Tag: git tag -a v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "  4. Push: git push && git push --tags"
echo "  5. Upload: twine upload dist/*"