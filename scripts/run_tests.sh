#!/bin/bash
# Run all tests with proper organization

set -e

echo "================================"
echo "Running Test Suite"
echo "================================"
echo ""

# Run unit tests
echo "1. Running Unit Tests..."
echo "------------------------"
pytest tests/unit/ -v -m unit || true
echo ""

# Run integration tests
echo "2. Running Integration Tests..."
echo "--------------------------------"
pytest tests/integration/ -v -m integration || true
echo ""

# Run existing tests
echo "3. Running Existing Tests..."
echo "----------------------------"
pytest tests/test_*.py -v || true
echo ""

# Run E2E tests (may be slow)
echo "4. Running E2E Tests..."
echo "-----------------------"
pytest tests/e2e/ -v -m e2e --timeout=300 || true
echo ""

echo "================================"
echo "Test Suite Complete"
echo "================================"
