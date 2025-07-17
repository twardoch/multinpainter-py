#!/bin/bash
# this_file: scripts/test.sh

set -e

echo "🧪 Running tests for multinpainter..."

# Install test dependencies
echo "📦 Installing test dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .[testing]

# Run linting if available
if command -v pre-commit &> /dev/null; then
    echo "🔍 Running pre-commit hooks..."
    pre-commit run --all-files || true
fi

# Run tests with coverage
echo "🧪 Running tests with coverage..."
python3 -m pytest tests/ -v --cov=multinpainter --cov-report=term-missing --cov-report=html

# Display coverage report location
echo "📊 Coverage report generated in htmlcov/index.html"

echo "✅ All tests completed!"