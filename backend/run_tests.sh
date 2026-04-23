#!/bin/bash
# Test runner script for the Automatic Email Responder

echo "=========================================="
echo "Automatic Email Responder - Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest is not installed"
    echo "Please install testing dependencies first:"
    echo "  pip install pytest pytest-cov pytest-mock Faker"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")"

echo "Running tests..."
echo ""

# Run tests with coverage
pytest tests/ -v --cov=services --cov=models --cov=routes --cov-report=term-missing --cov-report=html

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ All tests passed!"
    echo "=========================================="
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
else
    echo ""
    echo "=========================================="
    echo "✗ Some tests failed"
    echo "=========================================="
    exit 1
fi
